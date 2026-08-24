import logging
import re
from dataclasses import dataclass, field

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class PIIDetectionResult:
    cleaned_text: str
    detected: bool
    removed_counts: dict[str, int] = field(default_factory=dict)


class PIIRemover:
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.pii_enabled
        self.remove = self.settings.pii_remove
        self.confidence_threshold = self.settings.pii_confidence_threshold
        self.target_entities = set(self.settings.pii_entities)
        self.analyzer = None
        self._init_presidio()

    def _init_presidio(self):
        try:
            from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }
            nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

            # Custom Vietnamese Phone Recognizer
            vn_phone_pattern = Pattern(
                name="vn_phone_pattern",
                regex=r"(?:\+84|84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])\d{7}\b",
                score=0.9,
            )
            vn_phone_recognizer = PatternRecognizer(
                supported_entity="PHONE_NUMBER", patterns=[vn_phone_pattern], supported_language="en"
            )
            self.analyzer.registry.add_recognizer(vn_phone_recognizer)

            # Custom Vietnamese ID Recognizer (CCCD / CMND)
            vn_id_pattern = Pattern(name="vn_id_pattern", regex=r"\b(?:\d{9}|\d{12})\b", score=0.75)
            vn_id_recognizer = PatternRecognizer(
                supported_entity="ID_NUMBER", patterns=[vn_id_pattern], supported_language="en"
            )
            self.analyzer.registry.add_recognizer(vn_id_recognizer)

            # Vehicle Plate Recognizer
            vehicle_plate_pattern = Pattern(
                name="vehicle_plate_pattern", regex=r"\b\d{2}[A-Z1-9][-\s]?\d{4,5}\b", score=0.85
            )
            vehicle_plate_recognizer = PatternRecognizer(
                supported_entity="VEHICLE_PLATE", patterns=[vehicle_plate_pattern], supported_language="en"
            )
            self.analyzer.registry.add_recognizer(vehicle_plate_recognizer)

        except Exception as e:
            logger.info(f"Presidio Analyzer using regex-fallback engine: {e}")
            self.analyzer = None

    def process(self, text: str) -> PIIDetectionResult:
        if not text or not self.enabled:
            return PIIDetectionResult(cleaned_text=text or "", detected=False, removed_counts={})

        removed_counts: dict[str, int] = {}
        spans_to_remove: list[tuple[int, int, str]] = []

        # 1. Presidio Analyzer if available
        if self.analyzer:
            try:
                results = self.analyzer.analyze(text=text, language="vi")
                for r in results:
                    if r.entity_type in self.target_entities and r.score >= self.confidence_threshold:
                        spans_to_remove.append((r.start, r.end, r.entity_type))
            except Exception as e:
                logger.debug(f"Presidio analyze step error: {e}")

        # 2. Rule-based Regex Recognizers without variable-width lookbehinds
        vn_name_words = r"[A-ZÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-zàáảãạăắằẳẵặâấầuẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+"
        vn_full_name = f"{vn_name_words}(?:\\s+{vn_name_words})+"

        regex_rules = [
            ("EMAIL_ADDRESS", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", None),
            ("PHONE_NUMBER", r"(?:\+84|84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])\d{7}\b|\b0\d{9}\b", None),
            ("PERSON", r"(?:Khách hàng|KH|Ông|Bà|Anh|Chị|Họ và tên:|Họ tên:|KTV)\s+(" + vn_full_name + r")", 1),
            ("CREDIT_CARD", r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b", None),
            ("CUSTOMER_ID", r"\b(?:CUST|KH|CUSTOMER)[-_]?\d+\b", None),
            ("EMPLOYEE_ID", r"\b(?:EMP|NV|EMPLOYEE)[-_]?\d+\b", None),
            ("VEHICLE_PLATE", r"\b\d{2}[A-Z1-9][-\s]?\d{4,5}\b", None),
            ("PASSWORD", r"(?:mật khẩu|password|pass|pwd):\s*(\S+)", 1),
            ("USERNAME", r"(?:tên đăng nhập|tài khoản|username|user):\s*([A-Za-z0-9_.-]+)", 1),
            ("BANK_ACCOUNT", r"(?:STK|số tài khoản|tài khoản ngân hàng):\s*(\d{8,16})", 1),
            ("ID_NUMBER", r"(?:CCCD|CMND|số định danh|số ID):\s*(\d{9}|\d{12})", 1),
        ]

        for item in regex_rules:
            entity_type, pattern, group_idx = item
            if entity_type not in self.target_entities:
                continue

            flags = re.IGNORECASE if entity_type in ("CUSTOMER_ID", "EMPLOYEE_ID", "PASSWORD", "USERNAME") else 0
            for match in re.finditer(pattern, text, flags):
                if group_idx is not None:
                    try:
                        start, end = match.start(group_idx), match.end(group_idx)
                    except IndexError:
                        start, end = match.start(), match.end()
                else:
                    start, end = match.start(), match.end()

                spans_to_remove.append((start, end, entity_type))

        if not spans_to_remove:
            return PIIDetectionResult(cleaned_text=text, detected=False, removed_counts={})

        # Merge overlapping spans
        spans_to_remove.sort(key=lambda x: (x[0], x[1]))
        merged_spans: list[tuple[int, int, str]] = []
        for span in spans_to_remove:
            if not merged_spans:
                merged_spans.append(span)
            else:
                last_start, last_end, last_entity = merged_spans[-1]
                if span[0] < last_end:
                    new_end = max(last_end, span[1])
                    merged_spans[-1] = (last_start, new_end, last_entity)
                else:
                    merged_spans.append(span)

        # Build output string by removing PII spans
        last_idx = 0
        cleaned_parts = []
        for start, end, entity in merged_spans:
            cleaned_parts.append(text[last_idx:start])
            last_idx = end
            removed_counts[entity] = removed_counts.get(entity, 0) + 1

        cleaned_parts.append(text[last_idx:])
        cleaned_text = "".join(cleaned_parts)

        # Cleanup extra double spaces left by removal
        cleaned_text = re.sub(r"[ \t]{2,}", " ", cleaned_text)
        cleaned_text = re.sub(r" \n", "\n", cleaned_text)

        return PIIDetectionResult(
            cleaned_text=cleaned_text,
            detected=True,
            removed_counts=removed_counts,
        )

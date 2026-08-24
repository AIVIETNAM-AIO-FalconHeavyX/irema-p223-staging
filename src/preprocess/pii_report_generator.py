import json


class PIIReportGenerator:
    @staticmethod
    def generate_dict(document_id: str, pii_detected: bool, removed_entities: dict[str, int]) -> dict:
        """Generate PII report dict adhering to SPEC Section 15."""
        return {
            "document_id": document_id,
            "pii_detected": pii_detected,
            "removed_entities": removed_entities or {},
        }

    @staticmethod
    def generate_json(document_id: str, pii_detected: bool, removed_entities: dict[str, int], indent: int = 2) -> str:
        """Generate formatted JSON PII report string without original PII values."""
        report_dict = PIIReportGenerator.generate_dict(document_id, pii_detected, removed_entities)
        return json.dumps(report_dict, ensure_ascii=False, indent=indent)

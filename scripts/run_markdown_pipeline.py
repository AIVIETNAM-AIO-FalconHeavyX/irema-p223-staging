import argparse
import logging
import sys
from pathlib import Path

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preprocess.markdown_pipeline import MarkdownProcessingPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_markdown_pipeline")


def main():
    parser = argparse.ArgumentParser(
        description="Run Markdown Cleaning, Structure Normalization & Structure-aware Chunking Pipeline."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Path to a single markdown file to process.",
    )
    parser.add_argument(
        "--input-dir",
        "-i",
        type=str,
        help="Input directory containing markdown files (defaults to data/processed/markdown).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        help="Base processed output directory (defaults to data/processed).",
    )

    args = parser.parse_args()

    pipeline = MarkdownProcessingPipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )

    if args.file:
        file_path = Path(args.file)
        logger.info(f"Processing single file: {file_path}")
        result = pipeline.process_markdown_file(file_path)
        if result:
            out_md, out_chunks = result
            logger.info(f"DONE. Cleaned MD: {out_md}, Chunks: {out_chunks}")
        else:
            logger.error("Failed to process file.")
            sys.exit(1)
    else:
        logger.info(f"Batch processing all markdown files from: {pipeline.input_md_dir}")
        results = pipeline.run_all()
        logger.info(f"DONE. Successfully processed {len(results)} markdown files.")


if __name__ == "__main__":
    main()

"""CLI entrypoint to run Braintrust evaluations."""

import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.braintrust_eval import main

if __name__ == "__main__":
    main()

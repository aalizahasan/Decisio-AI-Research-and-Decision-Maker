import asyncio
import sys
import os

# Ensure backend root directory is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.evaluation.runner import run_evaluation_suite


def main():
    try:
        report = asyncio.run(run_evaluation_suite())
        if report["summary"]["failed"] > 0:
            sys.exit(1)
        sys.exit(0)
    except Exception as err:
        print(f"FATAL: Evaluation suite execution error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Usage: python3 run.py [path/to/file.las]"""
import sys
from wireline_qc.pipeline import main

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

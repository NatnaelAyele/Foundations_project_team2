import os
import sys
from pathlib import Path

import pytest


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    raise SystemExit(pytest.main([str(Path(__file__).parent), "-q"]))

import sys
from pathlib import Path

# Make `duck_connect` and the shared fakes importable without installing anything.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

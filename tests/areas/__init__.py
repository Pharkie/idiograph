"""The suite's areas, each a file of its own, aNNN_<name>.py holding test_<name>, which
tests/test_idiograph.py runs in its order, and support.py, what more than one of them uses. Loading
the package puts the app's folder first on the path, so an area imports the app's modules by their
names (17 October)."""
import sys
from pathlib import Path

_APP = str(Path(__file__).resolve().parents[2])
if _APP not in sys.path:
    sys.path.insert(0, _APP)

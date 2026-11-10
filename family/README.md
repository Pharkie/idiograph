# The family's code

What every app of the family shares (Idiograph, Sift and Trace). Each folder of the codebase is an import root: `boot.setup` puts this one and each served app's folder (`apps/<app>/`) on `sys.path`, so a module keeps its plain name wherever it sits. A module here never imports an app's: the boundary check (`tests/areas/a253_boundaries.py`) counts every crossing against `tests/boundaries.json`. See docs/internals.md, "The family's folders".

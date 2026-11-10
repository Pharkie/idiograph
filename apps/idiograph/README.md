# Idiograph's own code

Idiograph's own modules, and its `static/` files, the page's parts (`idiograph.html`), its scripts (`distil.js`, `themes.js`, `trajectories.js`) and styles (`distil.css`, `themes.css`), in an import root that `boot.setup` puts on `sys.path` when the run serves Idiograph. A module here imports the family's (`family/`) and Idiograph's own, never another app's. See docs/internals.md, "The family's folders".

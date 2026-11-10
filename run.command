#!/bin/bash
# Idiograph, macOS. Double-click this file in Finder, or run it from a terminal. run.sh beside it
# does the work: it finds the app's Python environment, and on the first run of a downloaded copy
# sets one up.
# Quit in Settings names this file as the way to open the app again
export IDIOGRAPH_START=run.command
exec /bin/bash "$(dirname "$0")/run.sh" "$@"

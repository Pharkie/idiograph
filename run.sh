#!/bin/bash
# Idiograph, macOS or Linux. Run it from a terminal, or double-click run.command on a Mac, which
# runs this file.
#
# The app's folder is this file's own. Its Python environment, .venv, is looked for beside it
# first, as a downloaded copy keeps it, and then two folders up, at the root of the repo the folder
# sits in, from where the server starts as it always has. With neither, the first run makes .venv
# beside it with the first Python it finds of 3.11 or later and installs openpyxl into it, so the
# second run starts at once. The setup is made under another name and takes the name .venv only
# once openpyxl is in it, so a setup that fails or is stopped never leaves a .venv behind.
HERE="$(cd "$(dirname "$0")" && pwd)" || exit 1
# the versions packaging/build_mac.py pins, so the app runs on the same openpyxl either way, and on
# the same et_xmlfile, which openpyxl writes with when there is no lxml, as GitHub's suite pins it
OPENPYXL="openpyxl==3.1.5"
ET_XMLFILE="et_xmlfile==2.0.0"
# and cryptography, which seals Working together's messages
CRYPTOGRAPHY="cryptography==50.0.2"
PYTHON_ORG="https://www.python.org/downloads/"
# Quit in Settings names the file the app was started from as the way to open it again
export IDIOGRAPH_START="${IDIOGRAPH_START:-run.sh}"

if [ -x "$HERE/.venv/bin/python3" ]; then
  cd "$HERE" || exit 1
  exec "$HERE/.venv/bin/python3" server.py "$@"
fi
if [ -x "$HERE/../../.venv/bin/python3" ]; then
  cd "$HERE/../.." || exit 1
  ROOT="$(pwd)"
  exec ".venv/bin/python3" "${HERE#"$ROOT"/}/server.py" "$@"
fi

# The first run. A Python of 3.11 or later: the one a terminal finds first, then a python.org
# install and Homebrew's on a Mac. OLD keeps the version of one too old, for the message.
FOUND=""
OLD=""
for CANDIDATE in python3 python /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 \
    /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  command -v "$CANDIDATE" >/dev/null 2>&1 || continue
  VERSION="$("$CANDIDATE" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)" || continue
  [ -n "$VERSION" ] || continue
  if "$CANDIDATE" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    FOUND="$CANDIDATE"
    break
  fi
  OLD="$VERSION"
done

if [ -z "$FOUND" ]; then
  if [ -n "$OLD" ]; then
    echo "Idiograph needs Python 3.11 or later, and the one on this computer is $OLD."
  else
    echo "Idiograph needs Python 3.11 or later, and there is none on this computer."
  fi
  echo "Install it from $PYTHON_ORG and open Idiograph again."
  exit 1
fi

echo "Setting up Idiograph, once. It takes a minute."
SETUP="$HERE/.venv-setup"
rm -rf "$SETUP"
if "$FOUND" -m venv "$SETUP" \
    && "$SETUP/bin/python3" -m pip install --disable-pip-version-check -q "$OPENPYXL" "$ET_XMLFILE" "$CRYPTOGRAPHY" \
    && rm -rf "$HERE/.venv" && mv "$SETUP" "$HERE/.venv"; then
  cd "$HERE" || exit 1
  exec "$HERE/.venv/bin/python3" server.py "$@"
fi
rm -rf "$SETUP"
echo "Idiograph could not set itself up, so nothing was kept. Check the internet connection and open it again."
exit 1

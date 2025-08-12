#!/usr/bin/env bash
set -euo pipefail

REPO_ZIP_URL="https://github.com/cbarria/gorilla/archive/refs/heads/main.zip"
INSTALL_PATH="${HOME}/gorilla"
RUN_APP=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-zip-url)
      REPO_ZIP_URL="$2"; shift 2 ;;
    --install-path)
      INSTALL_PATH="$2"; shift 2 ;;
    --run)
      RUN_APP=true; shift ;;
    *)
      echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

echo "Installing Gorilla to: ${INSTALL_PATH}" >&2
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

zipfile="$tmpdir/gorilla.zip"
echo "Downloading repo zip..." >&2
curl -fsSL "$REPO_ZIP_URL" -o "$zipfile"

echo "Extracting..." >&2
unzip -q "$zipfile" -d "$tmpdir"
extracted_dir=$(find "$tmpdir" -maxdepth 1 -type d -name 'gorilla-*' | head -n1)
if [[ -z "${extracted_dir}" ]]; then
  echo "Could not find extracted directory" >&2
  exit 1
fi

rm -rf "$INSTALL_PATH"
mkdir -p "$(dirname "$INSTALL_PATH")"
mv "$extracted_dir" "$INSTALL_PATH"

cd "$INSTALL_PATH"
echo "Creating venv..." >&2
python3 -m venv .venv

echo "Installing dependencies..." >&2
"$INSTALL_PATH/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"$INSTALL_PATH/.venv/bin/python" -m pip install -r requirements.txt

echo "Installed at $INSTALL_PATH" >&2
echo "To run: source \"$INSTALL_PATH/.venv/bin/activate\" && python src/gorilla.py" >&2

if $RUN_APP; then
  echo "Launching game..." >&2
  "$INSTALL_PATH/.venv/bin/python" src/gorilla.py
fi



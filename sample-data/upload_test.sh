#!/usr/bin/env bash
# Upload a test scenario folder to the Knight Insurance API and trigger processing.
# Usage: ./upload_test.sh <test-folder-path> [optional-label]

set -e

DIR="$1"
LABEL="${2:-$(basename "$DIR")}"
API="http://54.221.226.243:8000/api/submissions"

if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  echo "Usage: $0 <test-folder-path>"
  exit 1
fi

echo "=== Uploading: $LABEL ==="

# Build file args
FILES=""
for f in "$DIR"/*.pdf "$DIR"/*.xlsx; do
  [ -f "$f" ] && FILES="$FILES -F files=@$f"
done
for f in "$DIR"/driver-licenses/*; do
  [ -f "$f" ] && FILES="$FILES -F files=@$f"
done

# Upload
RESULT=$(eval curl -s -X POST "$API/upload" $FILES)
ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
DOCS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('document_count',0))" 2>/dev/null)

echo "  ID: $ID | Docs: $DOCS"

if [ -z "$ID" ]; then
  echo "  ERROR: Upload failed"
  echo "  $RESULT"
  exit 1
fi

# Trigger processing
curl -s -X POST "$API/$ID/process" > /dev/null 2>&1
echo "  Processing started..."
echo "$ID"

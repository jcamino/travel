#!/bin/bash
# usage: batch.sh listfile grep-regex  ; listfile lines: name|url
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1
while IFS='|' read -r name url; do
  [ -z "$name" ] && continue
  python fetch.py "$url" --links > "p_$name.txt" 2>&1
  sz=$(wc -c < "p_$name.txt")
  echo "=================== $name  ($sz bytes)  $(head -1 p_$name.txt)"
  if [ -n "$2" ]; then grep -n -E "$2" "p_$name.txt" | grep -v '^.*### LINKS' | head -${3:-25}; fi
done < "$1"

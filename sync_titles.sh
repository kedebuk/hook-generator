#!/bin/bash
cd /Users/kantor/hook-generator || exit 1
export PATH=/opt/homebrew/bin:$PATH
export GOG_KEYRING_BACKEND=file
export GOG_KEYRING_PASSWORD=$(grep ^GOG_KEYRING_PASSWORD= ~/.hermes/profiles/vex/.env|cut -d= -f2-)
gog sheets read 1rU06w_oKUb2DK6jCWyIbd4i6CaubCzY0JE3coOE7j0k "Sheet1!A2:I210" -p -a herbaheroninja@gmail.com > /tmp/tom.tsv 2>/tmp/tom.err
if [ ! -s /tmp/tom.tsv ]; then echo "gog read empty"; cat /tmp/tom.err; exit 1; fi
/opt/homebrew/bin/python3 /Users/kantor/hook-generator/build_titles.py
if [ -d .git ]; then
  if ! git diff --quiet titles.json 2>/dev/null; then
    git add titles.json
    git commit -q -m "sync titles $(date +'%F %H:%M')" && git push -q origin main 2>/dev/null
  fi
fi

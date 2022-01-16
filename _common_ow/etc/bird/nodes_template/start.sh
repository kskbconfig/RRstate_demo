#!/bin/bash
cd "$(dirname "$0")" || true
rm -r /etc/bird/nodes || true
mkdir -p /etc/bird/nodes
export DOLLAR='$'
for template in *.conf; do
    [ -f "$template" ] || continue
    nodename=${template::-5}
    if [[ $nodename == "$NODE_NAME" ]]; then
        continue
    fi
    conf=/etc/bird/nodes/${template}
    cat "$template" | sed -e 's/\${/＄/g' | sed 's/\$/${DOLLAR}/g' | sed 's/＄/${/g' | envsubst > "$conf"
done

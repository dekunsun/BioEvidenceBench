#!/usr/bin/env bash
# Watch one pod. Delete it through the API if (a) its results branch has appeared and the pod is
# still there 2 minutes later, or (b) it is still there after MAX_MIN minutes.
POD="$1"; MAX_MIN="$2"; STAGE="$3"; START=$(date +%s)
q() { curl -s -m 30 -X POST https://api.runpod.io/graphql -H "Content-Type: application/json" -d "$1"; }
before=$(cd /home/user/bioevidencebench && git ls-remote origin "refs/heads/rl-runs/*_${STAGE}" | cut -f2 | sort)
seen=""
while true; do
  el=$(( ($(date +%s) - START) / 60 ))
  st=$(q "{\"query\":\"query { pod(input:{podId:\\\"$POD\\\"}) { id desiredStatus } }\"}")
  echo "[$(date -u +%H:%M:%S)] ${el} min: $st" >> watch_${POD}.log
  if echo "$st" | grep -q '"pod":null'; then echo "pod ${POD} gone after ${el} min"; break; fi
  now=$(cd /home/user/bioevidencebench && git ls-remote origin "refs/heads/rl-runs/*_${STAGE}" | cut -f2 | sort)
  new=$(comm -13 <(echo "$before") <(echo "$now"))
  if [ -n "$new" ] && [ -z "$seen" ]; then seen=$(date +%s); echo "results branch: $new" >> watch_${POD}.log; fi
  if { [ -n "$seen" ] && [ $(( $(date +%s) - seen )) -ge 120 ]; } || [ "$el" -ge "$MAX_MIN" ]; then
    echo "pod ${POD} still there (${el} min, results branch: ${new:-none}): terminating"
    q "{\"query\":\"mutation { podTerminate(input:{podId:\\\"$POD\\\"}) }\"}"; sleep 20
    q "{\"query\":\"query { pod(input:{podId:\\\"$POD\\\"}) { id desiredStatus } }\"}"; break
  fi
  sleep 45
done
echo "new results branch: ${new:-none}"

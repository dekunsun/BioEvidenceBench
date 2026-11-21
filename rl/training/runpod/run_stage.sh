#!/usr/bin/env bash
# Module 7b: run one stage on a RunPod GPU pod and always clean up after it.
#
#   bash run_stage.sh <stage> <max_minutes> <usd_per_hour>
#   e.g. bash run_stage.sh stoptest 5 0.34
#
# Stages: stoptest (sleeps 60 s: tests saving, uploading and self-termination; first launch),
#         calibrate (stage 1, rl/training/stage1_calibrate.py),
#         smoke (stage 2, rl/training/stage2_smoke.py: short SFT and GRPO, throughput and cost).
#
# What it guarantees (Gloria, 2026-11-21):
# - A watchdog ends the stage after <max_minutes>, whatever the job is doing.
# - On success, error, timeout or a manual interrupt, the same finalise step runs: write
#   status.json (outcome, minutes, cost), save logs and results under /workspace, upload them to the
#   GitHub branch rl-runs/<run_id>, and CHECK the upload (the remote branch must hold the same commit).
# - Only after a checked upload is the pod deleted (no storage left to bill). If the upload fails,
#   the pod is STOPPED instead, so the volume /workspace keeps the results (billed about
#   $0.20/GB/month while stopped) for Gloria to fetch.
# - Secrets come only from RunPod Secrets as environment variables (GITHUB_TOKEN); nothing secret is
#   written to disk, printed or committed. The pod-scoped RUNPOD_API_KEY and RUNPOD_POD_ID are set by
#   RunPod in every pod.
# Self-stop and self-delete commands are not documented as such by RunPod: every variant tried and
# its output is logged, and the stoptest stage exists to see which one works.
set -uo pipefail

STAGE="${1:?stage}"; MAX_MIN="${2:?max minutes}"; PRICE="${3:?usd per hour}"
REPO_URL="https://github.com/dekunsun/BioEvidenceBench.git"
RUN_ID="$(date -u +%Y%m%d-%H%M)_${STAGE}"
WS="/workspace/rl_runs/${RUN_ID}"
REPO="/workspace/repo"
mkdir -p "$WS"
START=$(date +%s)
FINALISED=0
JOB_PID=""

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$WS/wrapper.log"; }

git_auth() {   # token passed through a credential helper: never in a URL, a log or a file
  git -c credential.helper= -c credential.helper='!f() { echo username=x-access-token; echo "password=${GITHUB_TOKEN}"; }; f' "$@"
}

pod_cmd() {    # $1 = stop | delete; tries each known form and logs what happened
  local action="$1" out
  for cmd in "runpodctl pod ${action} ${RUNPOD_POD_ID}" \
             "runpodctl $([ "$action" = delete ] && echo remove || echo stop) pod ${RUNPOD_POD_ID}"; do
    log "trying: ${cmd}"
    if out=$($cmd 2>&1); then log "ok: ${out}"; return 0; fi
    log "failed: ${out}"
  done
  local mutation; mutation=$([ "$action" = delete ] && echo podTerminate || echo podStop)
  log "trying: GraphQL ${mutation}"
  out=$(curl -s -X POST "https://api.runpod.io/graphql" -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
        -d "{\"query\":\"mutation { ${mutation}(input: {podId: \\\"${RUNPOD_POD_ID}\\\"}) }\"}" 2>&1)
  log "GraphQL answer: ${out}"
}

finalise() {
  local outcome="$1"
  [ "$FINALISED" = 1 ] && return
  FINALISED=1
  [ -f "$WS/TIMEOUT" ] && outcome="timeout"
  [ -n "${WATCHDOG_PID:-}" ] && kill "$WATCHDOG_PID" 2>/dev/null
  [ -n "$JOB_PID" ] && kill -TERM -- "-$JOB_PID" 2>/dev/null
  local secs=$(( $(date +%s) - START ))
  python3 - "$WS/status.json" "$outcome" "$secs" "$PRICE" "$STAGE" "$RUN_ID" <<'PY'
import json, os, sys
path, outcome, secs, price, stage, run_id = sys.argv[1:]
json.dump({"run_id": run_id, "stage": stage, "outcome": outcome, "minutes": round(int(secs) / 60, 2),
           "usd_estimate": round(int(secs) / 3600 * float(price), 4), "usd_per_hour": float(price),
           "pod_id": os.environ.get("RUNPOD_POD_ID"), "gpu": os.environ.get("RUNPOD_GPU_NAME", "")},
          open(path, "w"), indent=2)
PY
  log "outcome=${outcome} minutes=$((secs / 60))"
  nvidia-smi > "$WS/nvidia-smi.txt" 2>&1
  if [ -x /opt/rlvenv/bin/pip ]; then /opt/rlvenv/bin/pip freeze; else pip freeze; fi > "$WS/pip-freeze.txt" 2>&1

  local uploaded=0
  if [ -d "$REPO/.git" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
    for attempt in 1 2 3; do
      (
        cd "$REPO" && git checkout -q -B "rl-runs/${RUN_ID}" &&
        mkdir -p "rl/training/runs/${RUN_ID}" &&
        find "$WS" -maxdepth 1 -type f -size -20M -exec cp {} "rl/training/runs/${RUN_ID}/" \; &&
        git add "rl/training/runs/${RUN_ID}" &&
        git -c user.name="rl-pod" -c user.email="rl-pod@users.noreply.github.com" \
            commit -q -m "rl 7b run ${RUN_ID} (${outcome})" &&
        git_auth push -q origin "rl-runs/${RUN_ID}"
      ) >> "$WS/wrapper.log" 2>&1
      local local_sha remote_sha
      local_sha=$(git -C "$REPO" rev-parse HEAD 2>/dev/null)
      remote_sha=$(git_auth -C "$REPO" ls-remote origin "refs/heads/rl-runs/${RUN_ID}" 2>/dev/null | cut -f1)
      if [ -n "$local_sha" ] && [ "$local_sha" = "$remote_sha" ]; then uploaded=1; break; fi
      log "upload check failed (attempt ${attempt})"; sleep 10
    done
  else
    log "no repository or no GITHUB_TOKEN: nothing uploaded"
  fi

  if [ "$uploaded" = 1 ]; then
    log "upload checked (branch rl-runs/${RUN_ID}); deleting the pod"
    pod_cmd delete || pod_cmd stop
  else
    log "upload NOT confirmed; stopping the pod so /workspace keeps ${WS}"
    pod_cmd stop
  fi
}

trap 'finalise interrupted' INT TERM
trap 'finalise exit' EXIT

( sleep $(( MAX_MIN * 60 )); touch "$WS/TIMEOUT"; echo "[watchdog] ${MAX_MIN} min reached" >> "$WS/wrapper.log"
  kill -TERM $$ ) &
WATCHDOG_PID=$!
log "run ${RUN_ID}: stage=${STAGE} max=${MAX_MIN} min at \$${PRICE}/h on pod ${RUNPOD_POD_ID:-?}"
# Self-delete diagnostics, logged BEFORE the job so they reach the uploaded log (the first stage-1
# launch, started with a custom start command, could not delete itself). No secret is printed.
log "runpodctl: $(command -v runpodctl || echo missing); RUNPOD_API_KEY $([ -n "${RUNPOD_API_KEY:-}" ] && echo set || echo missing); RUNPOD_POD_ID ${RUNPOD_POD_ID:-missing}"
if [ -n "${RUNPOD_API_KEY:-}" ] && runpodctl config --apiKey "$RUNPOD_API_KEY" > /dev/null 2>&1; then
  log "runpodctl configured with the pod-scoped key"
fi
log "read check: $(runpodctl get pod "${RUNPOD_POD_ID:-x}" 2>&1 | head -2 | tr '\n' ' ' | cut -c1-200)"

# code: a fresh clone of main (read access is public or via the same token)
rm -rf "$REPO"
git_auth clone -q --depth 1 "$REPO_URL" "$REPO" >> "$WS/wrapper.log" 2>&1 || { log "clone failed"; exit 1; }
git -C "$REPO" rev-parse HEAD > "$WS/code_commit.txt"

run_job() {   # the job runs in its own process group so the watchdog can end all of it
  setsid bash -c "$1" >> "$WS/job.log" 2>&1 &
  JOB_PID=$!
  wait "$JOB_PID"
}

# Dependencies go into a fresh virtual environment, never the image's system Python: the second
# stage-1 launch failed because pip could not uninstall the image's Debian-installed PyJWT.
VENV=/opt/rlvenv
SETUP="cd '$REPO' && (python3 -m venv $VENV || (python3 -m pip install -q virtualenv && python3 -m virtualenv $VENV)) && \
       $VENV/bin/pip install -q --upgrade pip && $VENV/bin/pip install -q -r rl/training/runpod/requirements-gpu.txt"

case "$STAGE" in
  stoptest)
    run_job "nvidia-smi; sleep 60; echo stoptest-done > '$WS/result.txt'"
    ;;
  calibrate)
    run_job "$SETUP && $VENV/bin/python rl/training/stage1_calibrate.py --out '$WS'"
    ;;
  smoke)
    run_job "$SETUP && $VENV/bin/python rl/training/stage2_smoke.py --out '$WS' --price '$PRICE'"
    ;;
  *) log "unknown stage ${STAGE}"; exit 2 ;;
esac
code=$?
if [ "$code" = 0 ]; then finalise success; else finalise "error (exit ${code})"; fi

# Deploy one module-7b stage on RunPod through the GraphQL API (key injected by the network proxy).
# Usage: python3 deploy.py "NVIDIA GeForce RTX 4090" SECURE 0.89 calibrate 30
"""Deploy one module-7b pod through RunPod's GraphQL API (the key is injected by the network proxy)."""
import json, subprocess, sys
gpu, cloud, price, stage, minutes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
# /start.sh is the image's own start script (it sets up runpodctl, ssh and jupyter); run it in the
# background first, then our stage. The first stage-1 launch replaced it and could not self-delete.
start = ("bash -c '(/start.sh > /tmp/start.log 2>&1 &); sleep 20; curl -fsSL https://raw.githubusercontent.com/dekunsun/BioEvidenceBench/main/rl/training/runpod/run_stage.sh "
         f"-o /workspace/run_stage.sh && bash /workspace/run_stage.sh {stage} {minutes} {price}; sleep 30; "
         "runpodctl pod delete $RUNPOD_POD_ID || runpodctl remove pod $RUNPOD_POD_ID; sleep 900'")
q = """mutation Deploy($input: PodFindAndDeployOnDemandInput) {
  podFindAndDeployOnDemand(input: $input) { id name desiredStatus costPerHr machine { gpuDisplayName } }
}"""
inp = {"cloudType": cloud, "gpuCount": 1, "volumeInGb": 0, "containerDiskInGb": 50,
       "minVcpuCount": 2, "minMemoryInGb": 8, "gpuTypeId": gpu, "name": f"bioevidencebench-{stage}",
       "imageName": "runpod/pytorch:2.1.0-cu1320-torch280-ubuntu2404", "dockerArgs": start,
       "volumeMountPath": "/workspace",
       "env": [{"key": "GITHUB_TOKEN", "value": "{{ RUNPOD_SECRET_github_token }}"}]}
body = json.dumps({"query": q, "variables": {"input": inp}})
print(subprocess.run(["curl", "-s", "-m", "60", "-X", "POST", "https://api.runpod.io/graphql",
                      "-H", "Content-Type: application/json", "-d", body], capture_output=True, text=True).stdout)

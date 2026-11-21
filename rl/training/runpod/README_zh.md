# RunPod 操作说明（模块 7b）

GPU 总上限 **$20**，只用 RunPod。每次开机前 Claude 先报这一步的预计花费，你同意后再开。

## 一次性准备（约 10 分钟）

1. **充值不超过 $20，关闭自动续费（Auto-pay）。** RunPod 是预付费，这是最硬的上限：余额用完，所有 Pod 都会被停掉。
   注意：余额归零时，没有网络卷的 Pod 会被直接终止，数据无法恢复。所以别把余额用到 0，脚本里的计时器会提前收尾。
2. **在 GitHub 建一个细粒度 token**（Settings → Developer settings → Fine-grained tokens）：
   - 只选 `dekunsun/BioEvidenceBench` 一个仓库；
   - 权限只给 Contents: Read and write；
   - 有效期设短一些，比如 30 天。
3. **在 RunPod 的 Secrets 里保存这个 token**，名字叫 `github_token`。token 只存在 RunPod，不要发给 Claude，也不要贴进聊天或代码。

## 每次开机

1. Deploy 一台 **RTX 4090，Community Cloud**，模板选 RunPod PyTorch（任何带 Python 3 和 CUDA 的官方模板都可以）。
   - Container Disk 40 GB（要装 vLLM 和 torch），Volume Disk 20 GB；
   - 环境变量加一行：`GITHUB_TOKEN` = `{{ RUNPOD_SECRET_github_token }}`。
2. 打开 Web Terminal，粘贴 Claude 给你的命令。第一次是停机测试：

   ```bash
   curl -fsSL https://raw.githubusercontent.com/dekunsun/BioEvidenceBench/main/rl/training/runpod/run_stage.sh -o /workspace/run_stage.sh
   ```

   ```bash
   nohup bash /workspace/run_stage.sh stoptest 5 0.34 > /workspace/stoptest.out 2>&1 &
   ```

3. 终端可以关掉（`nohup` 保证任务继续跑）。脚本会自动做完这些事：
   - 跑完、出错、超时或被打断时，都先把日志和结果存到 `/workspace`；
   - 上传到 GitHub 分支 `rl-runs/<运行编号>`，并核对远端确实收到了；
   - 核对成功才**删除** Pod，不留存储费用；上传失败则只**停止** Pod，`/workspace` 里的结果保留。

## 停机测试要你确认的三件事（第一次必做）

停机测试大约 3–5 分钟，花费约 $0.03。跑完请看：

1. RunPod 控制台里这台 Pod 是否已经消失（被删除）。如果 5 分钟后还在运行，请手动 Terminate，然后告诉 Claude。
2. Billing 页面的扣费是否停在 Pod 消失的时间点。
3. GitHub 上是否出现了分支 `rl-runs/…_stoptest`，里面有 `status.json` 和 `wrapper.log`。

RunPod 文档没有写明 Pod 能否删除自己，脚本会依次尝试几种方式并全部记录在 `wrapper.log` 里。三件事都确认没问题，才开始阶段 1。

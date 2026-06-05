# CI 失败分析报告

## 基本信息
- PR: #2516 — 【自动升级】vllm-cpu容器镜像升级至0.22.1版本
- 失败类型: 无法确定（证据不足）
- 置信度: 低

## 根因分析

### 直接错误
CI 日志中**不包含**失败子任务的构建日志。触发 job（jenkins-from-comment）本身成功完成，但它触发的下游构建 `multiarch » openeuler » x86-64 » openeuler-docker-images #1361` 状态为 **FAILURE**，该构建的日志未在上下文中提供。

唯一可供分析的信息是触发 job 中输出的许可证/版权检查结果：
```
check result: ACL=[{"name": "check_sca", "result": 0}, {"name": "check_package_license", "result": 1}]
```
以及版权声明缺失告警：
```
the copyright in repo is not pass, notice: openeuler-docker-images/AI/vllm-cpu/meta.yml、
openeuler-docker-images/AI/vllm-cpu/README.md、
openeuler-docker-images/AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile、
openeuler-docker-images/AI/vllm-cpu/doc/image-info.yml文件缺失Copyright声明
```

### 根因定位
- 失败位置: 无法定位（缺少 `x86-64 » openeuler-docker-images #1361` 的构建日志）
- 失败原因: 下游 x86-64 构建 job 失败，但其详细日志缺失，无法确定根因

### 与 PR 变更的关联

PR 新增了一个 vLLM 0.22.1 的 Dockerfile（`AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile`），并更新了 README、image-info.yml、meta.yml。该失败与 PR 变更**高概率相关**，理由如下：

1. **架构差异**：aarch64 构建成功，x86-64 构建失败。可能原因包括：
   - Dockerfile 中 `pip install --extra-index https://download.pytorch.org/whl/cpu/ -r requirements/cpu.txt` 在 x86-64 上下载的 CPU-only PyTorch wheel 与 aarch64 不同，可能因版本不兼容或包不存在而失败
   - `VLLM_TARGET_DEVICE=cpu python3 setup.py bdist_wheel` 编译 vllm 时可能在 x86-64 上遇到特定编译错误
   - 网络/依赖下载环节在 x86-64 runner 上失败

2. **版权声明缺失**：新增的 4 个文件均缺失 Copyright 声明头，触发了 `check_package_license` 的 result=1（告警/失败），虽然触发 job 本身未因此阻断，但可能是下游构建失败的原因之一。

3. **历史模式匹配**：历史记录 PR #2512（同为 2026-06-05）与本案例高度相似——同样是 Dockerfile 新增导致的下游构建失败、同样缺少子任务构建日志、同样是 x86-64 架构失败而 aarch64 成功。该历史案例的根因是 Dockerfile 中 git 操作逻辑缺陷（浅克隆与 checkout 不兼容），本次 PR 的 Dockerfile 使用了 `git clone -b ${VERSION}` 而非直接指定 commit，逻辑上更安全，但仍可能存在类似的构建命令缺陷。

## 修复方向

### 方向 1（置信度: 低）
检查 Dockerfile 中 `pip install --extra-index https://download.pytorch.org/whl/cpu/ -r requirements/cpu.txt` 或 `VLLM_TARGET_DEVICE=cpu python3 setup.py bdist_wheel` 在 x86-64 上的执行结果，确认是否有依赖缺失、版本冲突或编译错误。

### 方向 2（置信度: 低）
检查 x86-64 构建节点的网络连通性，确认 `git clone` 和 `pip install` 在 x86-64 runner 上是否能正常下载外部资源。

### 方向 3（置信度: 低）
为新增文件添加 Copyright 声明头（Dockerfile、README.md、meta.yml、image-info.yml），排除 license 检查导致下游构建失败的可能性。

## 需要进一步确认的点

1. **获取 x86-64 构建日志**：这是最关键的一步。需要从 `multiarch » openeuler » x86-64 » openeuler-docker-images #1361` 获取完整构建日志，定位具体在哪一个 `RUN` 命令失败。
2. **对比 aarch64 日志**：aarch64 构建成功，对比两个架构的日志可快速定位差异点。
3. **验证 CPU-only PyTorch wheel 可用性**：确认 `https://download.pytorch.org/whl/cpu/` 上是否存在适配 vllm 0.22.1 所需 Python 版本和 x86-64 架构的 wheel。
4. **确认 `check_package_license` result=1 的语义**：该结果为告警还是硬性阻断？是否需要在下游构建中重新检查？

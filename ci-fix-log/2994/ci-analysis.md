# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器中断
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, closing transport, graceful_stop, no builder found, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7 `[2/4] RUN dnf install -y ...`（dnf 安装系统依赖阶段）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被外部触发优雅终止（`graceful_stop`），导致与构建器的 RPC 连接断开，`docker buildx` 无法继续执行。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及其相关元数据文件（README.md、image-info.yml、meta.yml），失败发生在 BuildKit 基础设施层面——构建器在下载系统 repo 元数据（`dnf install` 步骤）时被外部终止，不是由 Dockerfile 内容错误触发的。Docker 构建的所有已执行步骤（基础镜像拉取 `[1/4]`）均成功完成。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 CI 基础设施的 BuildKit 构建器异常中断（`graceful_stop`），与 PR 代码完全无关。通常重跑 CI Job 即可恢复，无需修改任何代码。

## 需要进一步确认的点
- 无。日志中 BuildKit 构建器优雅终止（`graceful_stop`）的证据充分，属于典型的 CI 基础设施间歇性故障。
- 若重试后仍持续失败，需排查 CI 环境中 BuildKit 构建器（`docker-container driver`）的稳定性，例如是否存在资源不足、超时自动回收、或节点调度策略导致构建器被提前清理。

## 修复验证要求
无需验证。此失败为 infra-error，Code Fixer 无需处理。

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 被终止
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found, buildx

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`，正在下载 openEuler 仓库元数据时（`OS 77 kB/s | 2.8 MB 00:37`）
- 失败原因: Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在构建进行中被意外终止（`graceful_stop`），导致与 builder 的 gRPC 连接断开（`closing transport`、`error reading from server: EOF`），后续无法找到该 builder 实例

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile（安装编译器工具链 + 编译 Python 3.9.19 + pip 安装 scann）和配套的元数据/文档文件。构建失败发生在最基础的 `dnf install` 阶段——尚未执行到任何与 PR 特定逻辑相关的步骤。Dockerfile 语法和内容本身没有问题。

失败是 CI 基础设施层面的问题：BuildKit builder 容器/服务在构建过程中被意外关停或被基础设施调度回收。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 CI 基础设施瞬态故障（BuildKit builder 被意外终止）。应重新触发 CI 流水线，让构建在健康的 builder 实例上重试。如果相同问题反复出现，需要排查 Jenkins 节点的 BuildKit builder 服务稳定性（如 builder 是否因 OOM 被 kill、是否有自动回收策略等）。

## 需要进一步确认的点
- 确认 `euler_builder_20260709_224657` 这个 builder 被终止的原因（Jenkins 节点日志 / BuildKit daemon 日志），是 OOM killed、超时回收还是手动操作
- 如果同一 PR 多次 retrigger 仍出现相同故障，需排查对应的 `ecs-build-docker-x86-hk` runner 节点的 BuildKit 配置是否有资源限制

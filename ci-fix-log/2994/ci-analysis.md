# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 终止
- 新模式症状关键词: `graceful_stop`, `closing transport`, `error reading from server: EOF`, `no builder ... found`, `rpc error: code = Unavailable`

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`，在 dnf 下载 OS 仓库元数据过程中（耗时约 38 秒，传输 2.8 MB，速度 77 kB/s）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被发送 `graceful_stop` 信号后主动关闭连接，导致 Docker 构建过程中断。`graceful_stop` 的 GOAWAY 调试数据表明这是 builder 的有意终止而非意外崩溃，可能是 CI 平台资源回收、builder 超时清理或基础设施运维操作所致。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了一个标准结构的 Dockerfile（安装编译依赖 → 编译 Python 3.9.19 → pip 安装 scann）、更新 README.md、image-info.yml 和 meta.yml。Dockerfile 内容本身没有语法错误或逻辑问题。失败发生在 CI 基础设施层——BuildKit builder 在 dnf 下载仓库元数据时被外部终止，这与 Dockerfile 的代码内容无关。类似的 scann Dockerfile（如 SP3 版本）在仓库中已有先例，构建命令模式一致。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI**。此类 `graceful_stop` 错误通常为 CI 基础设施的瞬时问题（builder 被清理/回收、网络抖动导致 gRPC 连接断开），重新运行 job 即可恢复。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
如果重试后仍然失败，可能需要检查 CI 平台是否有针对 builder 的运行时间限制或资源配额限制——dnf 元数据下载速度仅 77 kB/s 可能导致 builder 在镜像拉取/仓库同步阶段超时被回收。但此方向属于 CI 平台运维层面，Code Fixer 层面无法处理。

## 需要进一步确认的点
- BuildKit builder `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（CI 平台是否有 builder 生命周期管理策略或超时配置）
- 重试后是否仍然复现；如果复现，需要获取 CI 平台 builder 的管理日志确认终止原因

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder被终止
- 新模式症状关键词: graceful_stop, connection error, error reading from server: EOF, no builder found, buildx

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: CI 的 BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被优雅关闭（`graceful_stop`），导致 buildx 客户端与 builder 之间的 gRPC 连接断开，构建中断。这是 CI 基础设施层面的问题，与 Dockerfile 内容无关。

### 与 PR 变更的关联
**无关**。PR 新增的 Dockerfile 仅包含标准的系统包安装和 Python 编译步骤，构建失败时 `dnf install` 正在进行中（元数据正常下载，速度 77 kB/s），Dockerfile 语法和包名均无错误。失败原因完全是 BuildKit builder 被意外终止所致。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。由于 BuildKit builder 被 `graceful_stop` 终止属于 CI 基础设施的偶发性问题（可能由节点资源回收、调度超时、builder 健康检查失败等触发），不需要修改任何代码。重新运行 CI Job 大概率可以通过。

## 需要进一步确认的点
- Builder `euler_builder_20260709_224657` 被终止的具体原因：是 CI 节点资源不足（OOM）、builder 空闲超时自动回收、还是调度策略触发的主动下线。这些信息仅在 Jenkins 节点管理日志或 buildkit 守护进程日志中可见，当前提供的构建日志无法确认。

## 修复验证要求
无。本次失败为 infra-error，无需修改 Dockerfile 或任何代码文件。

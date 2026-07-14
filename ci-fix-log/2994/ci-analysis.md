# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, rpc error, connection error, EOF

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（正在下载 OS 元数据时）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被外部触发优雅终止（`graceful_stop`），导致 Docker 客户端与 builder 之间的 gRPC 连接断开（`connection error: EOF`），构建被迫中断。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 和对应的元数据文件（meta.yml、README.md、image-info.yml），Dockerfile 内容正确、结构合理。失败发生在 Docker build 基础设施层——BuildKit builder 在 `dnf install` 下载阶段被提前回收，属于 CI 平台的临时不稳定问题，不反映任何代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 CI 基础设施的瞬时故障（BuildKit builder 被提前回收）。直接重新触发 CI 构建即可，大概率会成功。如果持续复现，需要 CI 平台管理员排查 builder 实例的存活时间（TTL）配置是否过短，导致耗时较长的 `dnf install` 步骤尚未完成 builder 就被回收。

## 需要进一步确认的点
- builder `euler_builder_20260709_224657` 被优雅终止的具体原因（手动回收、超时回收、还是节点资源不足导致的驱逐）
- 若重试后仍然在同一位置失败，需要检查 `dnf install` 的网络连通性和 OS 仓库可达性（当前日志中 OS 元数据下载耗时 38.59 秒下载 2.8MB，速度正常，未出现超时）

## 修复验证要求
无需验证。本次失败属于 infra-error，不涉及任何代码修改，重试 CI 即可。

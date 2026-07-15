# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 连接丢失
- 新模式症状关键词: `failed to receive status`, `rpc error`, `graceful_stop`, `no builder found`, `docker-container driver`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段 `[2/4]`（`dnf install` 步骤）
- 失败原因: CI 的 Docker BuildKit builder（`euler_builder_20260709_224657`）在 `dnf install` 执行过程中被关闭（goaway 消息含 `graceful_stop`），导致 buildx 与 builder 之间的 gRPC 连接断开。后续重连时 builder 已不存在，构建失败。这是 CI 基础设施层面的问题（builder 容器被调度层终止或节点资源不足），与 PR 代码变更无关。

### 与 PR 变更的关联
**无关联**。PR 仅新增了一个标准格式的 Dockerfile（安装系统依赖 + Python + pip 安装 scann）和对应的元数据文件更新。失败发生在 Docker 构建的 `dnf install` 步骤，此时尚在安装基础系统包，尚未触及任何 PR 特有的构建逻辑。builder 崩溃为 CI 基础设施故障，即使重跑相同构建也可能成功。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 BuildKit builder 容器被意外终止导致的 infra-error，非代码层面问题。可以触发 CI 重新运行（如 `/retest` 或重新 push），大部分情况下重试即可通过。若反复出现同类错误，需由 CI 运维团队排查 builder 节点资源或调度策略。

## 需要进一步确认的点
- 如果重试后仍然失败，需检查 CI builder 节点（`ecs-build-docker-x86-hk`）的资源状况（内存/磁盘是否耗尽导致 builder 容器被 OOM Kill）。
- 确认是否有 CI 层面的超时配置导致 builder 在长时间 `dnf install` 期间被强制终止（日志中 `dnf` 仅运行约 38 秒，不似超时，但仍可排查）。

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable, connection error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install -y ...`（Dockerfile 第 8-10 行的 dnf install 命令执行期间）
- 失败原因: CI 构建所使用的 BuildKit daemon（`euler_builder_20260709_224657`）在构建过程中被外部调度系统优雅终止（`graceful_stop`），导致 Docker build 与 builder 之间的 gRPC 连接断开。该错误与 PR 代码变更无关，属于 CI 基础设施层面的瞬态故障。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 仅包含标准的 `dnf install` 编译依赖和 Python 源码编译步骤，没有任何异常操作。构建在 `dnf install` 执行到 38 秒时因 BuildKit builder 被外部关闭而中断——这发生在基础镜像已成功拉取、第一个 RUN 指令执行期间，与 Dockerfile 内容无关。`graceful_stop` 标志明确说明 builder 是被人为/调度系统主动停止的，而非因构建错误崩溃。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。此为 CI 基础设施瞬态故障（BuildKit daemon 被外部调度系统终止），PR 代码无需任何修改。直接 rerun failed job 即可验证。

## 需要进一步确认的点
- 该 CI runner（`ecs-build-docker-x86-hk`）上是否有资源配额限制或并发构建数上限，导致调度系统在资源紧张时主动终止正在运行的 BuildKit builder。
- 该时间点 CI 集群是否有其他大规模的构建任务调度或维护操作，导致 builder 被批量清理。

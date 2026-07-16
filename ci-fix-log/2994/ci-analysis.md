# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 失联
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建阶段，Dockerfile 步骤 `[2/4]`（`dnf install` 执行中）
- 失败原因: CI 所使用的 Docker BuildKit builder 实例（`euler_builder_20260709_224657`）在构建过程中被优雅关闭（`graceful_stop`），导致 `dnf install` 步骤运行时客户端与 builder 之间的 gRPC 连接断开（`rpc error: code = Unavailable`）。构建被迫中断时仅完成了基础镜像拉取和 `dnf install` 的部分元数据下载（约 38 秒），后续的 Python 编译和 scann pip 安装步骤均未到达。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（21 行），包含常规的 `dnf install`、`wget` Python 源码、`pip install scann` 三个构建步骤，以及 README、image-info.yml、meta.yml 的条目新增。Dockerfile 内容无语法错误或逻辑异常。构建失败发生在 Docker 构建基础设施层面（builder 实例被回收/关闭），非 PR 代码触发的错误。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是典型的 CI 基础设施瞬时故障，builder 节点在构建中途被调度器回收或遇到连接中断。无需修改任何代码或 Dockerfile，直接重试 CI 流水线即可。若反复出现相同错误，需联系 CI 基础设施运维排查 builder 节点稳定性或超时配置。

## 需要进一步确认的点
- 若同一 PR 多次重试均在同一阶段失败，需检查 CI 平台 builder 节点的资源配额（内存/磁盘）是否充足，以及 builder 保活超时（graceful stop timeout）是否过短。
- 确认 `euler_builder_20260709_224657` 实例的关闭原因（是否为 Jenkins job 超时、节点驱逐、或资源竞争所致）。

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被终止
- 新模式症状关键词: graceful_stop, closing transport, connection error: EOF, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器 `euler_builder_20260709_224657`（CI 基础设施层）
- 失败原因: Docker BuildKit 守护进程在执行 `dnf install`（构建步骤 [2/4]）期间收到 `graceful_stop` 信号被主动关闭，导致与构建器的 gRPC 连接断开，正在进行中的元数据下载（`dnf makecache`，2.8 MB，耗时约 37 秒）被中断，构建失败。

### 与 PR 变更的关联

**与 PR 代码变更无关。** 该 PR 仅新增了一个标准的 Dockerfile（安装 dnf 包 + 源码编译 Python 3.9.19 + pip 安装 scann）和更新了三个元数据文件（README.md、image-info.yml、meta.yml）。构建在 `dnf install` 的元数据下载阶段即因 CI 基础设施的 BuildKit 构建器被提前终止而失败，并未到达任何 PR 自定义的构建逻辑（Python 编译、pip 安装等）。Dockerfile 本身无语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败为 CI 基础设施问题——BuildKit 构建器 `euler_builder_20260709_224657` 在执行过程中被 `graceful_stop` 信号终止，属于 runner/构建器调度层面的临时性故障，与 PR 代码无关。重新触发 CI 流水线，使用新的构建器实例，预期可正常通过。

## 需要进一步确认的点
- BuildKit 构建器为何被 `graceful_stop` 终止（可能是 CI 节点资源回收、构建器超时策略触发、或运维操作导致）
- 若重试后仍失败，需进一步检查该 CI runner (`ecs-build-docker-x86-hk`) 的资源状态和 dnf 仓库网络连通性
- `dnf install` 元数据下载仅 77 kB/s（下载 2.8 MB 耗时 37 秒），网络较慢，若 CI 有 step 超时限制可能触发构建器终止

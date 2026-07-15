# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器断连
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建阶段 `#7 [2/4]`（`dnf install` 步骤），运行在 `ecs-build-docker-x86-hk` 节点
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被平台侧主动终止（`graceful_stop` with `NO_ERROR`），gRPC 传输连接随之中断，`dnf install` 下载 OS 仓库元数据至中途（2.8 MB，耗时 38+ 秒）时被强制终止

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）以及配套的 README.md、image-info.yml、meta.yml 更新，均为常规新增镜像的标准操作。Docker 构建在步骤 `#7 [2/4]`（`dnf install` 阶段）即因 BuildKit 构建器基础设施故障而中断，此时尚未执行到任何 PR 特有的构建逻辑（Python 编译、pip 安装 scann 等）。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 流水线。** 该失败为 BuildKit 构建器基础设施故障（构建器被平台主动终止），与 PR 代码完全无关。重新触发 CI 构建即可，无需修改任何文件。

## 需要进一步确认的点
- 构建器 `euler_builder_20260709_224657` 被 `graceful_stop` 的确切原因：是 CI 平台对构建器实例有超时限制（实例存活时间上限）、还是运行节点资源紧张导致调度器主动回收、或是平台侧运维操作触发的重启。
- 若反复重试仍因同样原因失败，需联系 CI 平台运维确认 `ecs-build-docker-x86-hk` 节点上 BuildKit 构建器的稳定性。

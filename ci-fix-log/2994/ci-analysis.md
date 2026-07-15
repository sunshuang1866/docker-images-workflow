# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 实例丢失
- 新模式症状关键词: no builder found, rpc error, closing transport, graceful_stop, connection error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS 77 kB/s | 2.8 MB 00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install` 下载 OS 元数据阶段）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被终止/丢失，导致 gRPC 连接断开（`graceful_stop`），构建无法继续

### 与 PR 变更的关联
**与 PR 变更无关。** 这是一个 CI 基础设施故障——BuildKit builder 实例在 dnf 下载软件包元数据过程中意外终止。PR 新增的 Dockerfile 本身逻辑无问题：基础镜像拉取成功（step #6 DONE），`dnf install` 的包列表正常（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel 均为 openEuler 标准仓库合法包名）。构建失败发生在 dnf 从仓库下载元数据期间，而非某个包安装失败或命令语法错误。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施恢复后重新触发构建即可。这类 Builder 实例丢失通常由 runner 资源不足、节点回收、或 BuildKit 守护进程重启导致，属于临时性 infra 故障。无需修改任何代码或 Dockerfile。

## 需要进一步确认的点
- Builder 实例 `euler_builder_20260709_224657` 被终止的具体原因（节点 OOM、配额耗尽、kubernetes pod 驱逐等），需检查 CI 平台该时间段的节点事件日志
- 日志仅显示了 x86-64 runner 的构建，若 aarch64 runner 上也有并行构建，其日志也需确认（但从 meta.yml diff 看未设置架构约束，可能存在 aarch64 构建，应一并检查其状态）

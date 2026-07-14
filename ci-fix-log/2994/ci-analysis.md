# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder, closing transport, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 正在下载仓库元数据时）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被外部系统发送 `graceful_stop` 信号终止，导致与构建器的 gRPC 连接断开（`closing transport due to connection error: EOF`），后续操作无法找到该构建器。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准 Dockerfile（安装系统包 → 编译 Python 3.9.19 → pip 安装 scann）和相关元数据条目，不涉及任何会导致构建器崩溃的特殊操作。构建在 `dnf install`（系统包安装）步骤被中断，这是 CI Runner 上的 BuildKit 构建器实例被外部原因（如资源回收、节点维护、进程 OOM 等）强制终止所致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是一个 CI 基础设施故障，应重新触发 CI 构建。如果该问题重复出现，需排查 CI Runner（`ecs-build-docker-x86-hk`）上的 BuildKit daemon 是否因资源不足（内存/磁盘）或节点调度策略导致 `graceful_stop`，由 CI 运维团队处理。

## 需要进一步确认的点
- 该 CI Runner 节点 `ecs-build-docker-x86-hk` 在同时间段是否有其他构建任务导致资源竞争。
- 重新触发 CI 后问题是否复现；若复现，需检查 BuildKit daemon 日志确认 `graceful_stop` 的触发来源（人工终止、OOM killer、还是调度平台自动回收）。

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（dnf install 安装编译依赖阶段）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 dnf 元数据下载过程中被服务端主动关闭（`graceful_stop`，HTTP/2 GOAWAY frame），连接断开后 Docker 构建无法继续，报 "no builder found"。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 语法正确，`dnf install` 命令中列出的依赖包（gcc、gcc-c++、make、wget、openssl-devel、bzip2-devel、zlib-devel）均为 openEuler 仓库中的标准包名。构建器在 `dnf` 下载仓库元数据期间被 CI 基础设施关闭，而非 Dockerfile 指令执行报错。该失败属于 CI 环境问题（构建节点资源/构建器生命周期管理），非代码层面的缺陷。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 运行。BuildKit 构建器 `graceful_stop` 通常由以下基础设施原因触发：
- CI 构建节点资源不足（内存/磁盘压力），调度器回收构建器
- 构建器空闲/运行超时阈值管理过于激进
- CI 节点上的 `buildkitd` 守护进程因 OOM、磁盘满等原因主动退出

Dockerfile 本身无需修改，应关注 CI 运行环境稳定性。建议重试 CI 或请求运维排查 `ecs-build-docker-x86-hk` 节点状态。

## 需要进一步确认的点
- 该 CI 节点 `ecs-build-docker-x86-hk` 在构建时间段（2026-07-09 22:46 UTC+8）是否存在资源告警或 `buildkitd` 进程重启记录。
- 同一时段其他 PR 的 x86-64 构建是否也出现同类 `graceful_stop` 错误（若是，则确认节点故障；若否，可能是偶发问题）。
- `euler_builder_20260709_224657` 构建器的生命周期管理策略：是否存在硬性超时限制了该步骤的最大执行时间。

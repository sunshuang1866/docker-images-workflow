# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器异常终止
- 新模式症状关键词: `failed to receive status`, `rpc error`, `Unavailable`, `graceful_stop`, `no builder found`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker buildx 构建阶段，步骤 `#7 [2/4]`（dnf install），无具体 Dockerfile 行号
- 失败原因: CI 使用的 buildkit 构建器实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中异常终止（`graceful_stop`），导致 RPC 连接中断。该构建器实例在 `dnf install` 下载软件包阶段被关闭，随后查无此实例（`no builder found`）

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个标准的 Dockerfile（安装编译依赖 → 编译 Python 3.9 → pip 安装 scann）、更新了 README.md、image-info.yml 和 meta.yml。所有变更均遵循项目既有模板，不包含任何可能触发构建器崩溃的非标准操作。故障发生在 BuildKit 基础设施层（构建器实例被终止），而非 Dockerfile 执行层（无语法错误、无依赖缺失、无编译失败）。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 这是典型的构建基础设施短暂故障（runner 上的 buildkit 守护进程被重启、资源不足导致构建器被驱逐、或网络抖动导致 RPC 连接断开）。PR 代码无需任何修改，重新触发 CI 流水线即可。

## 需要进一步确认的点
- 确认 CI runner `ecs-build-docker-x86-hk` 在构建时段是否有资源压力（内存/磁盘不足导致 buildkit 容器被 OOM-kill 或驱逐）
- 确认 buildkit 构建器实例 `euler_builder_20260709_224657` 是否为该 runner 上的共享资源，是否被其他并发构建任务影响
- 如果重试后仍然失败，需要获取 buildkit 守护进程端日志（而非客户端 RPC 错误）以确定 `graceful_stop` 的根本原因

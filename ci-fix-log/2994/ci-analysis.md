# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit实例被终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 阶段），在执行 openEuler 24.03-lts-sp4 基础镜像的软件包元数据下载时（38.59 秒处）
- 失败原因: CI 基础设施中的 BuildKit 容器化构建器实例 `euler_builder_20260709_224657` 被优雅终止（`graceful_stop`），与构建客户端的 gRPC 连接随即断开（`EOF`），导致 Docker 构建中断

### 与 PR 变更的关联
**无关**。本次 PR 新增的 Dockerfile 语法正确，符合项目规范。失败发生在 `dnf install` 的第一阶段——操作系统软件包元数据下载过程中，此时尚未进入 PR 引入的任何自定义步骤（Python 编译、pip install scann）。该错误完全由 CI 基础设施层事件（构建器实例被回收/超时/手动终止）引起，非代码变更导致。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 流水线**。该失败为偶发性基础设施问题（BuildKit 构建器实例在构建中途被终止），与 PR 代码变更无关。直接重跑 CI Job 即可。若重复出现同一错误，则需联系 CI 基础设施团队排查构建器实例的生命周期管理（超时阈值、资源配额、节点回收策略）。

### 方向 2（置信度: 低）
若重试后仍然失败且错误相同，需排查 CI runner 节点（`ecs-build-docker-x86-hk`）上的 BuildKit 配置，确认是否存在针对特定基础镜像（`openeuler/openeuler:24.03-lts-sp4`）或特定 dnf 仓库访问的限流/超时策略。

## 需要进一步确认的点
- 该 CI runner 节点（`ecs-build-docker-x86-hk`）在同一时间段是否有其他构建任务也出现相同错误（判断是单点故障还是系统性问题）
- 构建器实例的存活时间（TTL）配置是否小于本次 dnf 元数据下载所需时间（当时下载速率仅 77 kB/s，持续 37 秒才完成 2.8 MB 元数据，完整包安装可能需更长时间）
- 是否为构建器实例的节点资源（内存/磁盘）耗尽导致 kubelet/dockerd 主动回收

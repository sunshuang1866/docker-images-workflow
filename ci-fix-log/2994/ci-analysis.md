# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: closing transport, graceful_stop, no builder found, buildx, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`，`dnf install` 下载 OS 元数据阶段（~38 秒处）
- 失败原因: CI 的 BuildKit builder 容器（`euler_builder_20260709_224657`）在 Docker 构建过程中被优雅关闭（`graceful_stop`），导致 buildx 客户端与 builder 的连接断开，构建中断。这是 CI 基础设施层面的问题，与 PR 的代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`，其 `dnf install` 命令语法和包名均正确（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）。失败发生在 dnf 下载元数据的第 38 秒，BuildKit builder 进程被外部终止，而非 dnf 命令本身的错误。PR 中的 Dockerfile、README.md、image-info.yml、meta.yml 变更均无语法或逻辑问题。

## 修复方向

### 方向 1（置信度: 中）
**无需修改 PR 代码。** 该失败属于 CI 基础设施问题（BuildKit builder 被终止），应重新触发 CI 构建。如果反复出现，需排查 CI runner 节点的 BuildKit 服务稳定性或资源限制（如 builder 容器被 OOM kill 或超时清理策略触发）。

## 需要进一步确认的点
1. CI runner 节点（`ecs-build-docker-x86-hk`）上 BuildKit builder 容器为何被 `graceful_stop`——是被 OOM killer 终止、达到了超时限制，还是被上层编排系统主动清理？
2. 如果重试后依然在同一阶段失败，需确认 dnf 安装这些基础包时是否存在特定网络或仓库访问问题（当前日志中 dnf 正在正常下载元数据，未出现报错）。
3. 确认 openEuler 24.03-lts-sp4 基础镜像的仓库中是否确实存在 `openssl-devel`、`bzip2-devel`、`zlib-devel` 这些包名（openEuler 中部分包名可能与标准 CentOS/RHEL 命名有差异，但当前日志未到达包解析阶段，无法验证）。

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器连接中断
- 新模式症状关键词: rpc error, Unavailable, closing transport, EOF, graceful_stop, no builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 下载 OS 元数据阶段）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中被服务端主动关闭（GOAWAY frame，debug data 为 `graceful_stop`），导致 BuildKit 客户端 RPC 连接中断，后续检查 builder 实例时已不可用。这是一个 CI 基础设施层面的问题，与 PR 的代码变更无关。

### 与 PR 变更的关联
PR #2994 的变更（新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`、更新 README.md、image-info.yml、meta.yml）均为常规的 openEuler 镜像支持追加操作。Dockerfile 中的 `dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel` 命令语法正确，构建在下载 OS 包元数据阶段（38.59 秒，下载 2.8 MB）因 BuildKit 构建器被基础设施层回收而中断，与 PR 代码无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。这是 BuildKit 构建器实例被服务端 `graceful_stop` 回收导致的偶发性基础设施故障，通常在资源调度、超时回收或构建节点维护期间发生。重新触发流水线（retry）大概率可以成功通过。

## 需要进一步确认的点
- 若重新触发后仍然失败在同一位置（`dnf install` 阶段），需检查 CI 构建节点的资源配额（内存/磁盘）、dnf 仓库网络可达性及构建超时配置。
- 该构建运行在 `ecs-build-docker-x86-hk` 节点上，若该节点存在稳定性问题，可考虑切换构建节点重试。

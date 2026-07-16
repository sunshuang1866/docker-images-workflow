# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被关停
- 新模式症状关键词: graceful_stop, no builder found, error reading from server: EOF, closing transport

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 #7（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 dnf 安装软件包过程中被主动关停（`graceful_stop`），导致 gRPC 传输连接中断（`error reading from server: EOF`），Docker 构建进程无法继续。该 builder 随后已不存在（`no builder found`），无法恢复。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增一个 scann Dockerfile（基于 openEuler 24.03-lts-sp4 安装 gcc、Python 3.9.19、scann 1.4.2 的 pip 包）及配套的 README、meta.yml、image-info.yml 条目。构建器在 dnf 安装基础依赖阶段即被基础设施侧关停，Dockerfile 中的 `RUN dnf install` 指令语法和包名均正确，不存在导致构建器崩溃的代码缺陷。失败原因为 CI 基础设施问题（构建器被调度系统回收/超时关闭）。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 该失败为 CI 基础设施故障，BuildKit builder 实例在构建过程中被意外关停。建议重试 CI job，联系 CI 平台运维排查 builder 健康检查策略（是否存在超时自动回收、资源配额触顶驱逐等机制）。

## 需要进一步确认的点
- CI 构建集群中 BuildKit builder 的资源配额（内存/磁盘）是否充足
- 是否存在 builder 空闲超时策略，在 dnf 下载元数据期间将 builder 标记为不活跃并回收
- 该 build executor 节点（`ecs-build-docker-x86-hk`）上是否有其他并发构建竞争资源导致 builder 被驱逐

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用（infra-error，无需代码修复）。

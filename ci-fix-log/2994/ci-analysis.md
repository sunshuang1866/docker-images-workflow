# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 被终止
- 新模式症状关键词: graceful_stop, no builder found, rpc error, closing transport, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段 `[2/4]` — `RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 镜像构建过程中被终止（`graceful_stop`），导致构建连接断开（`error reading from server: EOF`）。`goaway` 原因为 `NO_ERROR`，说明非构建报错触发的终止，而是 builder 节点自身因外部原因（如节点池调度回收、资源预占释放等）被主动关闭。

### 与 PR 变更的关联
**无关。** PR 仅新增了一个 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile（共 21 行），加上 README.md、image-info.yml、meta.yml 的配套元数据更新。构建失败发生在 dnf 安装系统包（gcc、openssl-devel 等）的**基础设施层**，而非 Dockerfile 指令本身的语法或逻辑错误。这些包名在 openEuler 仓库中均为标准包，且同类 Dockerfile（如 scann 1.4.2 的 24.03-lts-sp3 版本）使用相同依赖可正常构建。Builder 的 `graceful_stop` 与 PR 代码无因果关联。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试（re-trigger）。** 此为 BuildKit 基础设施瞬时故障，builder 节点被外部终止（可能因节点池缩容、Spot 实例回收等）。PR 代码本身无需修改。重新触发 CI pipeline 即可。如果多次重试均在同一位置失败，则需要排查 builder 节点资源（内存/磁盘）是否不足以完成 dnf 安装步骤。

## 需要进一步确认的点
- 若重试后持续失败，需排查 `ecs-build-docker-x86-hk` 节点在该时段的资源水位（内存、磁盘空间），确认 dnf 安装 (os 仓库 metadata 2.8MB + 包下载) 是否因磁盘不足触发 builder 被 kill。
- 确认该 Jenkins agent `ecs-build-docker-x86-hk` 是否在对应时段有节点池回收事件。

## 修复验证要求
无需代码修复，重试 CI 构建即可。若重试后通过，则确认属于 infra-error；若持续失败，需获取 builder 节点的系统日志进一步排查。

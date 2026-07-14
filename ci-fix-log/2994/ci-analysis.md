# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 被终止
- 新模式症状关键词: goaway, graceful_stop, no builder found, euler_builder, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Dockerfile `[2/4] RUN dnf install ...` 步骤（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile:8`）
- 失败原因: BuildKit 的 `docker-container` 驱动 builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被**优雅终止**（`graceful_stop` goaway），导致正在执行的 `dnf install` 步骤的 gRPC 连接断开，构建器无法恢复。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 的 `RUN dnf install ...` 步骤语法正确、包名合理（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`），与同仓库其他同类 Dockerfile（如 `24.03-lts-sp3` 版本）的依赖声明模式一致。

失败发生在 BuildKit 基础设施层——builder 实例在 dnf 下载元数据过程中（进度 37 秒，已下载 2.8 MB）被外部主动终止，属于 CI runner/节点层面的问题。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。这是一个典型的 CI 基础设施瞬时故障，BuildKit builder 被 `graceful_stop` 终止的常见原因包括：
- CI runner 节点资源紧张触发 OOM killer / 自动清理
- Jenkins 的 build timeout 机制在 Docker 构建步骤超时前终止了 builder
- Runner 节点维护/调度触发了容器清理

由于 Dockerfile 本身逻辑无问题（依赖声明正确、步骤顺序合理），重新提交构建大概率可以成功。如果重试仍失败在同一位置，则可排查是否是 dnf 下载阶段耗时过长（openEuler 24.03-LTS-SP4 镜像首次 pull 后 `dnf` 需要下载约 2.8 MB 元数据 + 安装多个 `-devel` 包），可考虑在 Dockerfile 中添加 `--setopt=timeout=300` 等 dnf 超时参数缓解。

### 方向 2（置信度: 低）
**检查 Jenkins job 的构建超时配置**。如果该 Jenkins job 对单个 Docker 构建步骤设定了较短的超时，而 `dnf install`（含元数据下载）在网络波动下耗时逼近阈值，可能触发了 builder 的优雅终止。可从 Jenkins 侧调整 `Build step 'Execute shell'` 的超时设置，或为 `docker buildx build` 命令添加 `--builder` 参数的显式超时控制。

## 需要进一步确认的点
1. Jenkins 构建节点的资源使用情况（内存/磁盘）在 builder 被终止时刻是否触达限制
2. 同批次其他镜像的构建是否也出现相同失败（判断是单节点问题还是集群性问题）
3. `euler_builder_20260709_224657` 是否因 Jenkins node 的 idle cleanup 策略被回收
4. 确认是否存在对 `docker buildx build` 或 `docker-container` driver 的显式超时限制

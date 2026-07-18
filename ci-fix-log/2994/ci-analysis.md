# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器终止
- 新模式症状关键词: failed to receive status, rpc error, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（x86-64 构建节点 `ecs-build-docker-x86-hk`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建进行到 `dnf install` 阶段时，收到服务端 GOAWAY 信号（`graceful_stop`）被终止，导致 gRPC 连接断开，构建无法继续。

### 与 PR 变更的关联
PR 仅新增了一个标准结构的 Dockerfile（安装系统依赖 → 编译 Python 3.9.19 → pip 安装 scann）及配套的 README、image-info.yml、meta.yml 条目。构建失败发生在最基础的 `dnf install` 步骤，与 PR 代码变更无直接关联。该 Dockerfile 本身不存在语法错误或逻辑问题。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施的瞬时故障（BuildKit builder daemon 被服务端优雅关闭）。建议**触发 CI 重试（re-run）**，大概率可成功通过。若多次重试仍失败，需检查 CI 节点上 BuildKit builder 实例的健康状态和资源配额。

## 需要进一步确认的点
1. CI 节点 `ecs-build-docker-x86-hk` 上 BuildKit daemon（`euler_builder_*`）是否存在资源不足、OOM 或被其他 Job 抢占的问题。
2. 同批次其他 PR 的构建是否也出现相同错误——如果是，则确认是集群级别的基础设施问题。
3. 该 PR 的 aarch64 构建 job 是否成功，以排除 Dockerfile 在多架构上的潜在问题（根据日志，当前失败仅发生在 x86-64 job）。

# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器崩溃
- 新模式症状关键词: graceful_stop, no builder found, closing transport, euler_builder, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器 `euler_builder_20260709_224657`
- 失败原因: CI 构建过程中，Docker BuildKit 构建器实例（`euler_builder_20260709_224657`）在执行 Dockerfile 第 2/4 步（`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）期间被异常终止（`graceful_stop`），导致 gRPC 传输连接中断（`EOF`），后续尝试重连时构建器已不存在（`no builder found`）。这是一次 CI 基础设施层面的故障，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了标准化的 Dockerfile（安装编译工具链 + Python 3.9.19 + pip 安装 scann）、更新 README.md、image-info.yml 和 meta.yml。Dockerfile 内容、语法和构建步骤均无异常——基础镜像拉取成功（步骤 1/4 完成），失败发生在 BuildKit 构建器进程自身崩溃，与 PR 代码逻辑无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需代码修复。等待 CI 基础设施恢复后重新触发构建即可。BuildKit 构建器 `graceful_stop` 通常由宿主机资源不足、OOM killer、或 docker-container 驱动实例被外部终止导致。

## 需要进一步确认的点
- 确认 CI 构建节点 `ecs-build-docker-x86-hk` 在构建时刻是否存在资源耗尽（内存/磁盘）或 BuildKit 守护进程异常重启的情况。
- 确认是否有其他 PR 在同一时段出现相同的 BuildKit builder 崩溃问题——若为普遍现象，需运维介入排查 BuildKit 集群健康状态。

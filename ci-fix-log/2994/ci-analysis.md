# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 意外终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install ...`（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被意外终止（`graceful_stop` goaway），导致 `dnf install` 步骤的 gRPC 传输连接断开，构建进程失去与 builder 的连接后报 `no builder found`

### 与 PR 变更的关联
**与 PR 代码变更无关。** 此次失败是 CI 基础设施层面的问题——BuildKit builder 进程在 `dnf install` 下载元数据阶段被意外终止。PR 新增的 Dockerfile 本身没有语法或逻辑错误，构建刚开始执行第一个 `RUN` 指令（安装编译依赖）时就遇到了 builder 崩溃。这属于 CI runner / buildkit 资源回收、超时或节点不稳定的问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施故障，Code Fixer 无需对 Dockerfile 或任何代码文件做修改。建议重新触发 CI 流水线重试。如果多次重试均在同一位置失败，则需检查 CI 构建节点（`ecs-build-docker-x86-hk`）的 BuildKit daemon 健康状态和资源配额。

## 需要进一步确认的点
- CI 构建节点 `ecs-build-docker-x86-hk` 上的 BuildKit daemon 是否存在资源不足（内存/磁盘）或超时自动回收策略
- 同一时间段是否有其他构建任务也因 builder 意外终止而失败（判断是单点故障还是系统性资源问题）
- `graceful_stop` 的触发来源——是 BuildKit daemon 主动发送还是上层编排系统（如 Jenkins plugin）触发了 builder 清理

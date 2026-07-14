# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器意外终止
- 新模式症状关键词: failed to receive status, rpc error, closing transport, goaway, graceful_stop, no builder found

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4] RUN dnf install ...`（OS 元数据下载阶段）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 OS 软件包元数据时被意外终止（`graceful_stop` goaway 帧），导致 gRPC 连接断开，构建无法继续

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）及相关元数据和文档。Dockerfile 内容为常规的依赖安装和 Python/Scann 编译流程，语法正确，不存在导致 BuildKit 构建器崩溃的逻辑。构建在第一个 `dnf install` 命令的 OS 元数据下载阶段就已因构建器基础设施故障而失败，属于 CI 环境问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** BuildKit 构建器 `euler_builder_20260709_224657` 在构建过程中向客户端发送了 `graceful_stop` goaway 帧后关闭连接，这不是代码问题。可能的原因包括：
- CI runner 资源不足（内存/磁盘耗尽导致 BuildKit 构建器被 OOM killer 终止）
- 构建器会话超时（日志显示 dnf 下载元数据速率仅 77 kB/s，下载 2.8 MB 耗时约 37 秒，若构建器设置了较短的 idle 超时可能在此阶段超时）
- CI runner 节点瞬时不稳定

直接重新触发 CI 构建即可，无需修改任何代码。

### 方向 2（置信度: 低）
若多次重试均在同一位置失败，可能需排查 CI runner 的 BuildKit 构建器配置（如超时阈值、资源限制）或 runner 节点的网络/存储健康状况。

## 需要进一步确认的点
- 本次构建所在的 runner 节点 `ecs-build-docker-x86-hk` 是否存在资源压力（内存/磁盘不足）
- BuildKit 构建器的 `--timeout` 配置是否过短，导致在低速网络下（77 kB/s）`dnf install` 被判定为超时并触发 graceful_stop
- 是否需要获取 aarch64 架构的构建日志以确认是否两个架构均失败（日志仅展示了 x86-64 job 的信息）

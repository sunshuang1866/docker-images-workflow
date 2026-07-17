# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器连接断开
- 新模式症状关键词: failed to receive status, rpc error, closing transport, graceful_stop, no builder found, docker-container driver

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install`），发生在 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`
- 失败原因: Docker BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载元数据过程中被优雅关闭（goaway frame 携带 `graceful_stop`），导致 RPC 连接断开，后续构建步骤无法继续。**此失败与 PR 代码变更无关，是 CI 基础设施层面的问题。**

### 与 PR 变更的关联
**无关。** PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。`dnf install` 命令语法正确、包名均有效，且该命令已正常开始执行（metadata 已开始下载，速度 77 kB/s）。失败发生在 BuildKit 基础设施层——构建器容器在构建中途被外部因素终止，非 Dockerfile 或 `dnf` 命令本身导致。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此失败是 CI 基础设施问题（BuildKit 构建器异常终止）。建议：
- 检查 CI 环境中 BuildKit builder 的生命周期管理策略，确认是否存在自动清理/回收机制在构建进行中误终止 builder
- 重新触发 CI 运行（retry），大概率可以正常通过

### 方向 2（置信度: 中）
如果多次重试均在同一 `dnf install` 步骤失败，需排查构建节点的资源情况（磁盘空间、内存压力），`dnf` 元数据下载速度仅 77 kB/s 表明网络状况较差，长时间运行可能触发 builder 空闲超时。

## 需要进一步确认的点
- BuildKit builder `euler_builder_20260709_224657` 被 `graceful_stop` 终止的具体原因（是否为 CI 编排层的 builder 生命周期管理策略导致）
- 构建节点的网络带宽和磁盘空间是否充足（metadata 下载速度仅 77 kB/s）
- 是否存在 builder 的最大运行时间限制（timeout）被触发

## 修复验证要求
不适用（infra-error，无需代码修改）。

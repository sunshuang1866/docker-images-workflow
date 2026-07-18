# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器中断
- 新模式症状关键词: `failed to receive status`, `graceful_stop`, `no builder`, `rpc error: code = Unavailable`, `closing transport`

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install -y ...`（dnf 正在下载 OS 元数据时）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 dnf 安装阶段被终止（`graceful_stop`），连接断开后无法再找到该构建器，导致 Docker build 失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相关元数据文件，Dockerfile 内容为标准的 dnf 包安装和 Python 编译流程。失败发生在 dnf 正在下载元数据时（构建步骤 2/4），BuildKit 构建器在约 38 秒后主动发送 `graceful_stop` 信号并断开连接——这是 CI 基础设施层面的问题（构建器被回收/超时/资源不足终止），而非 Dockerfile 内容或 PR 改动引起。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施故障（BuildKit 构建器异常终止），**Code Fixer 无需处理此 PR 的代码**。建议在 CI 侧重新触发构建（retry），大多数情况下重新运行即可通过。如果重试后仍然失败，需要排查构建节点的资源状况或构建器 TTL 配置。

## 需要进一步确认的点
- 构建节点（`ecs-build-docker-x86-hk`）在构建期间是否存在资源压力（内存/磁盘不足）导致构建器被 OOM Killer 终止
- BuildKit 构建器 `euler_builder_20260709_224657` 的 TTL/超时配置，是否存在构建超时自动回收机制
- 同一时间段内同一节点上其他构建 job 是否也出现相同问题（判断是单点故障还是系统性问题）

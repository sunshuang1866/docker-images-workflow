# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit 构建器被基础设施优雅关闭
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, buildkit, Unavailable

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段，步骤 [2/4]（dnf install 包安装），正在下载 OS 包元数据
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被 CI 基础设施优雅关闭（`graceful_stop`），导致 Docker 构建连接中断，构建器实例随后被回收

### 与 PR 变更的关联
本次 PR 仅新增 scann 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Dockerfile 内容为标准流程（安装编译依赖、编译 Python、pip 安装 scann），无语法或逻辑问题。构建失败发生在 dnf 包下载阶段，BuildKit 构建器因外部基础设施原因被终止，**与 PR 代码变更无关**。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。BuildKit 构建器被基础设施优雅关闭属于偶发性 CI 环境问题，常见原因包括：CI 节点资源不足、构建器超时被回收、节点维护等。重新触发构建后大概率通过。

## 需要进一步确认的点
- 如果多次重试仍失败，需确认 CI 节点 `ecs-build-docker-x86-hk` 是否有资源瓶颈（内存/磁盘不足）
- 确认是否存在构建超时配置（dnf 包下载在网络不佳时可能耗时较长）

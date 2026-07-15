# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 构建器被提前终止
- 新模式症状关键词: `graceful_stop`, `no builder`, `rpc error`, `closing transport`, `connection error`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器的 dnf 包管理器元数据下载阶段（Dockerfile 第 2/4 步）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在 dnf 下载仓库元数据过程中被优雅终止（`graceful_stop` + `NO_ERROR`），导致与构建器的 RPC 连接断开（`connection error: EOF`）。构建器终止后，后续查询报 `no builder found`。

### 与 PR 变更的关联
与 PR 变更**无关**。构建在步骤 #7（dnf install 下载阶段）即被中断，尚未执行到步骤 #8（编译 Python 3.9.19）和步骤 #9（pip install scann），因此无法评估 Dockerfile 内容是否正确。PR 仅新增了一个标准 Dockerfile 和元数据/README 条目，不存在可能导致构建器崩溃的代码逻辑问题。该失败属于 CI 基础设施层面，`graceful_stop` debug 信息表明这是构建器的主动/被动资源回收行为（如超时、节点下线、资源配额耗尽等），与 PR 代码内容无关。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 构建。该失败为 BuildKit 构建器在构建过程中被终止的 infra-error，非代码问题。若重新构建后仍失败，则可进一步判断是构建超时还是 Dockerfile 本身存在问题。建议关注构建节点资源状态（磁盘、内存、构建超时阈值）。

## 需要进一步确认的点
-  构建器被 `graceful_stop` 终止的具体原因：是 CI 构建超时阈值触发、节点资源不足、还是调度系统主动回收？需要查看 CI 调度器/集群管理日志确认。
-  dnf 下载仓库元数据耗时 38+ 秒是否异常（可能为网络波动导致下载变慢，触发了某种超时机制）。
-  若重新构建后仍失败，需获取完整日志以排除 Dockerfile 中 dnf 包源配置或网络连通性问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无。本失败为 infra-error，不涉及代码修复。

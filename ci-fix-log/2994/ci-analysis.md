# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 被终止
- 新模式症状关键词: failed to receive status, rpc error, Unavailable, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 下载 OS 元数据阶段）
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被基础设施层面主动终止（`graceful_stop` + `NO_ERROR`），导致 Docker 构建连接中断，随后构建器实例已不存在（`no builder found`）。这不是代码或 Dockerfile 本身的问题，而是 CI 基础设施对构建器实例的外部终止操作。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了 scann 1.4.2 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），均为标准文件。基础镜像拉取成功（`#6 DONE 2.9s`），`dnf install` 步骤在下载元数据时被基础设施强行终止，与 Dockerfile 内容无因果关联。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败是由 CI 基础设施（BuildKit builder 被终止）引起的偶发性问题，Dockerfile 本身无错误。直接重试 CI（例如在 PR 中 push 一个空 commit 或 `/retest`）即可。

## 需要进一步确认的点
- 构建器 `euler_builder_20260709_224657` 被终止的具体原因（是否为 CI 平台资源调度、节点维护或构建超时所触发）。此信息仅在 CI 平台基础设施日志中可查，与代码仓库无关。

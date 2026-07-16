# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Builder被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, buildkit, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建 step `[2/4]` — `dnf install` 阶段（非 PR 代码文件内）
- 失败原因: Docker buildx builder 实例 `euler_builder_20260709_224657` 在构建过程中被优雅终止（graceful_stop），客户端与 builder 之间的 gRPC 连接断开，导致构建无法继续。该错误与 PR 的代码变更无关，属于 CI 基础设施层面的问题。

### 与 PR 变更的关联
**无关。** PR 变更内容为新增 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及相关元数据文件。构建失败发生在 `dnf install` 安装基础编译依赖阶段（步骤 2/4），此时尚未执行到 `pip install scann` 等与 scann 直接相关的步骤。该 `dnf install` 命令为标准操作，不存在语法或版本问题。builder 被终止是 CI 运行时的环境事故。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** builder 实例 `euler_builder_20260709_224657` 的 `graceful_stop` 表明其被 CI 调度系统或宿主机主动回收（可能原因：节点资源不足被驱逐、构建超时、或宿主机维护操作）。此错误为瞬时基础架构故障，重新运行 CI 大概率可以成功通过。Code Fixer 无需对代码做任何修改。

## 需要进一步确认的点
- 无。该失败的证据充分且明确指向基础设施层，不涉及 PR 代码问题。

## 修复验证要求
无需满足。该失败为 infra-error，不涉及对 PR 代码或外部源文件的任何修复。

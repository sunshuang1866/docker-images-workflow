# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 异常终止
- 新模式症状关键词: `failed to receive status, graceful_stop, no builder found, euler_builder, closing transport`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4] RUN dnf install`（Dockerfile 第 7-9 行）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 OS 元数据过程中被优雅终止（`graceful_stop`），导致与构建器的 gRPC 连接断开（`error reading from server: EOF`），后续并报告"找不到该 builder"。这是 CI 基础设施层面的故障，非 PR 代码变更或 Dockerfile 问题所致。

### 与 PR 变更的关联
**无关**。PR 新增了一个标准的 Dockerfile（为 scann 1.4.2 添加 openEuler 24.03-LTS-SP4 支持），其 `RUN dnf install` 命令是常规的系统包安装操作，格式正确且无语法错误。构建在 dnf 下载 RPM 仓库元数据的中间阶段因构建器被外部终止而失败，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
这是一个 CI 基础设施问题，无需对代码做任何修改。应重新触发 CI 流水线（re-run/re-trigger），若新的构建器实例不再被提前终止，构建应能正常完成。若反复出现同一错误，则需要 CI 运维团队排查 BuildKit 构建器节点 `euler_builder_*` 是否配置了过短的超时限制、资源不足自动回收策略，或节点本身存在稳定性问题。

## 需要进一步确认的点
- 构建器 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（是 CI 调度器的超时回收策略、节点资源压力自动驱逐，还是手动终止）。
- 同一时段是否有其他 PR 也遭遇了相同的 BuildKit builder 断开问题（判断是系统性故障还是偶发事件）。

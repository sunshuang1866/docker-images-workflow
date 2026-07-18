# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器崩溃
- 新模式症状关键词: no builder found, closing transport, graceful_stop, rpc error, connection error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 构建器基础设施（`euler_builder_20260709_224657`）
- 失败原因: BuildKit 构建器实例在 Docker 构建过程中被优雅关闭（`graceful_stop` + `NO_ERROR` goaway），导致正在执行的构建步骤（`dnf install`）因传输中断而失败，随后构建器实例已不存在（`no builder found`）

### 与 PR 变更的关联
**与 PR 无关**。该失败发生在 BuildKit 基础设施层面。日志显示构建器在 `dnf install` 步骤执行约 38 秒后被外部信号触发的 `graceful_stop` 关闭，而非 `dnf` 命令本身报错。PR 中新增的 Dockerfile 内容是常规的 `dnf install` + `wget` + `pip install` 流程，不会触发 BuildKit 守护进程的优雅关闭。该 PR 重跑 CI 大概率直接通过。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 CI 基础设施的临时故障（BuildKit 构建器意外关闭），建议重试 CI 流水线。Code Fixer 无需处理。

## 需要进一步确认的点
- BuildKit 构建器 `euler_builder_20260709_224657` 被关闭的原因（可能是 CI 节点资源回收、定时清理任务、或 Docker daemon 重启）。此信息通常在 CI 平台管理日志中查看，非 PR 代码层面可解决。

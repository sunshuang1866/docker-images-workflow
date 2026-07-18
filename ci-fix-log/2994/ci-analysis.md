# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 掉线
- 新模式症状关键词: graceful_stop, no builder found, closing transport, connection error, rpc error

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build step `[2/4]`（`dnf install` 阶段）
- 失败原因: CI BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被发送 `graceful_stop` 信号后终止，导致 Docker 构建连接的 gRPC 传输层中断（EOF），构建进程无法继续。

### 与 PR 变更的关联
此次失败与 PR 代码变更**无关**。PR 仅新增了一个标准 scann Dockerfile（安装 gcc/gcc-c++/make/wget 及 -devel 包、从源码构建 Python 3.9.19、pip 安装 scann）、更新了 README、image-info.yml 和 meta.yml。构建失败发生在 `dnf install` 这一基础设施操作阶段，且直接原因是 BuildKit builder 进程被终止（graceful_stop），属于 CI 基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
无需修改任何代码。这是一次 CI 基础设施的瞬时故障（BuildKit builder 进程意外终止）。建议重新触发 CI 构建流水线，极大概率直接通过。如果持续复现，需联系 CI 运维团队排查 builder 节点的稳定性或资源配额。

## 需要进一步确认的点
- BuildKit builder `euler_builder_20260709_224657` 被 `graceful_stop` 终止的具体原因（可能为 CI 编排层的 builder 回收策略、节点资源耗尽、或 builder 超时自动清理）。
- 该 builder 节点在 2026-07-09 22:46 前后是否有 OOM 事件或其他异常日志（CI 日志中未见 OOM 信号，仅见 graceful_stop）。

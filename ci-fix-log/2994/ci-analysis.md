# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit builder 连接中断
- 新模式症状关键词: graceful_stop, closing transport, error reading from server: EOF, no builder found, gRPC Unavailable

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`dnf install` 阶段），构建进行约 39 秒时
- 失败原因: Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被优雅关闭（`graceful_stop`），gRPC 传输层连接断开（`error reading from server: EOF`），导致构建中断。`no builder found` 为后续连锁错误。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了一个标准 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`），安装 Python 3.9.19 并用 pip 安装 scann 1.4.2。Dockerfile 内容没有明显错误，构建在 `dnf install` 常规下载阶段因 BuildKit 基础设施故障中断，而非因代码问题。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施故障——BuildKit builder 进程意外终止或被外部信号关闭。Code Fixer 无需处理。建议重新触发 CI 流水线重试构建，若多次重试均在同一位置失败，则需排查 runner 节点（`ecs-build-docker-x86-hk`）上 BuildKit daemon 的稳定性或资源限制（OOM、磁盘空间等）。

## 需要进一步确认的点
- 检查 runner 节点 `ecs-build-docker-x86-hk` 的系统日志（`dmesg`/`journalctl`），确认是否存在 OOM killer 或其他资源事件导致 BuildKit builder 被终止
- 确认 BuildKit builder `euler_builder_20260709_224657` 是否由外部编排进程主动回收
- 若多次重试后问题持续，需排查 Docker daemon 或 buildx 版本兼容性

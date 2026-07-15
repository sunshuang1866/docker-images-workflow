# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 意外终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, rpc error, Unavailable, EOF

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: 构建阶段 Docker 步骤 #7 [2/4]（`RUN dnf install -y gcc gcc-c++ make wget ...` 执行期间）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 `dnf install` 下载 OS 仓库元数据过程中被意外终止（debug data 显示 `graceful_stop`），导致 CI worker 与构建器之间的 gRPC 连接断开（EOF），后续尝试查找该 builder 时已不存在。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile（安装系统依赖 → 编译 Python 3.9.19 → pip 安装 scann）、更新 README、image-info.yml 和 meta.yml。构建在 Dockerfile 的第 2 步（`dnf install` 系统包）即中断，且中断原因为 BuildKit builder 进程被外部终止（`graceful_stop`），并非 Dockerfile 内任何命令执行失败。此前已成功完成：
- 代码克隆与差异检测（正确识别 4 个变更文件）
- 构建器创建
- 基础镜像拉取（`openeuler/openeuler:24.03-lts-sp4`）

这些步骤均表明 Dockerfile 本身语法有效、基础镜像可用。

## 修复方向

### 方向 1（置信度: 高）
此为 CI 基础设施问题，Code Fixer 无需处理。`graceful_stop` 表示 BuildKit builder 容器/进程被外部信号终止——常见于 CI 节点资源不足（OOM）、Docker 守护进程重启、或 builder 会话超时被清理。建议重新触发 CI 流水线重试即可。

## 需要进一步确认的点
- 确认 CI 构建节点（`ecs-build-docker-x86-hk`）在对应时间段的资源状态（内存、磁盘）及 Docker 守护进程日志，以排查 builder 被终止的具体原因（如 OOM Killer、磁盘空间不足、buildkit 超时配置等）。
- 如果重试后反复出现同类错误，需检查 CI 节点上 BuildKit builder 的生命周期配置（如 `--keep-session-time` 等参数）。

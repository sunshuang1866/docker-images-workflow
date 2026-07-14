# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 崩溃
- 新模式症状关键词: failed to receive status, rpc error, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker BuildKit 运行时（非 Dockerfile 内某个具体步骤）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载软件包阶段（约 38 秒后）被**优雅关闭**（`graceful_stop` goaway），导致与 builder 的 gRPC 连接断开（`EOF`），整个 Docker 构建过程被中断。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套的 README 和 meta 文件更新。构建流程已正确启动：基础镜像 `openeuler/openeuler:24.03-lts-sp4` 已成功拉取（`#6 DONE 2.9s`），`dnf install` 步骤也在正常运行中。失败完全是由 CI 基础设施层面的 BuildKit builder 进程意外终止所致，与 Dockerfile 内容、依赖包列表、或任何代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，**无需修改 Dockerfile 或 PR 代码**。需要检查 Jenkins 构建节点的 BuildKit builder 稳定性：
- 查看 `ecs-build-docker-x86-hk` 节点在 `22:46` 前后是否发生了 builder 进程重启、OOM 或其他资源异常
- 该 builder 实例 `euler_builder_20260709_224657` 是本次构建临时创建的，`graceful_stop` 表明可能是外部管理操作（如节点清理脚本）主动终止了它
- **建议操作**: Re-run the CI job，若重试后通过则确认是偶发 infra 波动

## 需要进一步确认的点
- `ecs-build-docker-x86-hk` 节点在 `2026-07-09 22:46:55` 前后是否存在 builder 清理脚本或自动回收策略导致 `euler_builder_20260709_224657` 被终止
- 是否有其他并发 job 导致资源争抢迫使 builder 进程退出
- 该节点是否曾出现过类似的间歇性 builder 丢失问题

## 修复验证要求
不适用（infra-error，无需代码修复）。

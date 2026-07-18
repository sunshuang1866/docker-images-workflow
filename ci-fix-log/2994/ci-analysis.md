# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Builder连接意外断开
- 新模式症状关键词: graceful_stop, no builder found, failed to receive status, rpc error, connection error, EOF

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: BuildKit builder 实例 `euler_builder_20260709_224657` 在执行 `dnf install` 下载 OS repo 元数据过程中被意外关闭（`graceful_stop`），导致 gRPC 连接断开，Docker 构建中断。这是 CI 基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 语法正确，依赖声明完整。Docker build 在下载阶段（未到达任何 Dockerfile 指令执行阶段）因 builder 意外终止而失败，PR 改动不触发该失败。

## 修复方向

### 方向 1（置信度: 高）
该失败为 CI 基础设施问题（BuildKit builder 实例异常终止），与 PR 代码无关。Code Fixer 无需修改任何文件。建议：
- 在 CI 系统中重新触发该 job 重试（retry），若 builder 恢复正常则构建应能通过。
- 若重试后仍反复出现，需要 CI 运维团队排查 `ecs-build-docker-x86-hk` 节点上 BuildKit builder 的稳定性问题（如资源耗尽、OOM kill、超时回收等）。

## 需要进一步确认的点
- 日志中无 Dockerfile 指令执行失败的信息，构建卡在 builder 连接层面，证据充分，无需额外确认。

## 修复验证要求
无需验证。本次失败为 infra-error，修复方向不涉及代码或 Dockerfile 修改。

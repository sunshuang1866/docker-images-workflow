# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 连接中断
- 新模式症状关键词: no builder, graceful_stop, closing transport, rpc error, euler_builder

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `[2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`
- 失败原因: Docker BuildKit builder 实例 `euler_builder_20260709_224657` 在构建过程中被优雅终止（`graceful_stop`），导致 gRPC 传输层连接中断。构建正执行到 `dnf` 下载 OS 元数据阶段（已运行约 38 秒，下载至 2.8 MB）时 builder 失联，随后 builder 实例被完全移除（`no builder ... found`）。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 Dockerfile（安装 gcc、openssl-devel 等常见构建依赖），并更新了元数据文件（README.md、image-info.yml、meta.yml）。故障发生在 CI 基础设施层——BuildKit builder 进程被终止，并非由 Dockerfile 内容或 PR 代码变更触发。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，Code Fixer 无需处理。建议重新触发 CI job。若重复出现，需检查 CI runner（`ecs-build-docker-x86-hk`）上 BuildKit builder 的生命周期管理配置：builder 实例是否因超时、资源配额或 runner 节点回收策略被提前销毁。

## 需要进一步确认的点
- builder `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（CI runner 超时配置、BuildKit builder 空闲回收策略、节点资源压力）
- 该 runner（`ecs-build-docker-x86-hk`）在相近时间段是否有其他构建任务竞争资源
- 同一 PR 在重新触发后是否能正常通过

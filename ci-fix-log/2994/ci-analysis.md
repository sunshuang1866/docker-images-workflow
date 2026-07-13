# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: BuildKit Builder 断连
- 新模式症状关键词: closing transport, rpc error, Unavailable, no builder found, graceful_stop

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4]`（`dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 期间被优雅关闭（graceful_stop），导致 Docker 构建连接中断，构建失败。

### 与 PR 变更的关联
此次失败与 PR 代码变更**无直接关联**。PR 新增的 Dockerfile 在语法和逻辑上均正确：
- 基础镜像 `openeuler/openeuler:24.03-lts-sp4` 成功拉取并解压
- `dnf install` 步骤开始执行，在下载 OS 元数据阶段 BuildKit builder 被外部因素终止

失败根因为 CI 基础设施问题——BuildKit 远程 builder 实例在构建中途被关闭。

## 修复方向

### 方向 1（置信度: 低）
**重新触发 CI 构建**。由于此次失败疑似为临时性的 CI 基础设施问题（builder 实例意外终止），且 PR 代码本身无明显问题，最直接的验证方式是 re-run 该 CI job。若重新构建后通过，则可确认本次为偶发性 infra 故障。

## 需要进一步确认的点
1. **BuildKit builder 被 graceful_stop 的原因**：日志中 `debug data: "graceful_stop"` 表明 builder 实例是被主动关闭的，而非崩溃。需要确认是否是 CI 平台对该 builder 设置了超时限制被触发、资源回收策略导致、还是运维人员手动终止。
2. **是否存在跨架构 job 日志**：当前提供的日志为 x86-64 架构的构建日志。若 CI pipeline 包含 aarch64 等架构的并行构建 job，需确认其他架构的构建状态是否也失败，以判断是否为全域性基础设施问题。
3. **重试是否复现**：若 rerun 后仍然在同一位置失败，需进一步排查 `dnf install` 步骤是否因网络超时或镜像源不可达导致 builder 空闲超时被 kill，而非代码层面的问题。

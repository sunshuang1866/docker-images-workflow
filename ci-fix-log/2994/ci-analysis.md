# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器中途终止
- 新模式症状关键词: failed to receive status, error reading from server: EOF, graceful_stop, no builder found, euler_builder

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 阶段），约执行 38.6 秒时
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 过程中被终止（`graceful_stop`），导致 BuildKit RPC 连接断开，后续 `docker buildx` 命令无法找到该构建器

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增了一个 Dockerfile 和三个元数据文件（README.md、image-info.yml、meta.yml），构建流程仅执行到 `dnf install` 阶段（安装 gcc、gcc-c++、make 等基础工具）即因基础设施问题中断，远未触及任何与 PR 改动相关的业务逻辑。失败是因为 CI 的 BuildKit 构建器 Pod/实例意外终止。

## 修复方向

### 方向 1（置信度: 中）
**无需代码修改。** 这是 CI 基础设施层面的问题——BuildKit 构建器 `euler_builder_20260709_224657` 在构建过程中被终止。可能原因：
- CI 构建节点资源不足（内存/磁盘），BuildKit 容器被 OOM Killer 或资源管理器终止
- 构建器实例有生存时间限制（TTL），超时后被自动清理
- 基础设施层面的计划内维护或节点回收

建议在 CI 系统中重新触发该 job，若重试后通过则确认为此类 transient infra 问题。

### 方向 2（置信度: 低）
若重试后仍在相同步骤失败（`dnf install` 阶段），可能是 `openeuler:24.03-lts-sp4` 基础镜像的 `dnf` 获取元数据时消耗过多内存/时间，导致 BuildKit 构建器超时。此种情况下可考虑在 `dnf install` 前增加 `dnf makecache` 或添加 `--setopt=timeout=300` 等超时参数。

## 需要进一步确认的点
- 确认 `ecs-build-docker-x86-hk` 构建节点的资源使用情况（在构建失败时间段是否有资源水位告警）
- 确认 BuildKit 构建器 `euler_builder_20260709_224657` 的 TTL 配置是否足以完成完整构建
- 重试该 job 观察是否稳定复现还是偶发

## 修复验证要求
无需验证。此问题为 CI 基础设施故障，不涉及对 Dockerfile 或任何仓库代码的修改。

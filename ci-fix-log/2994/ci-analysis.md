# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器意外终止
- 新模式症状关键词: graceful_stop, error reading from server: EOF, no builder found, closing transport

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建步骤 `[2/4]`（`dnf install` 阶段），非 PR 代码文件中
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建过程中被意外终止（`graceful_stop`），导致 gRPC 连接断开（`EOF`），正在进行中的 `dnf install` 步骤中断。构建器消失后，后续重连尝试报 `no builder found`。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 内容正确——基础镜像拉取成功（`#6 DONE 2.9s`），构建流程正常进入 `dnf install` 步骤。失败点是 CI 基础设施层的 BuildKit builder 在 `dnf install` 执行过程中被意外回收/重启，纯属 Runner 侧的环境问题。Dockerfile 本身无语法或逻辑错误。

## 修复方向

无需 Code Fixer 处理。此为 CI 基础设施临时故障（BuildKit builder 被 `graceful_stop`），应通过 CI 平台的 **重试机制** 解决，即重新触发该 PR 的 CI pipeline。

## 需要进一步确认的点

1. BuildKit builder `euler_builder_20260709_224657` 为何被 `graceful_stop`——可能是宿主机资源紧张触发 OOM、Runner 维护重启、或 docker-container driver 的 builder 超时回收。
2. 若重试后仍反复出现同类错误，需要排查 CI Runner `ecs-build-docker-x86-hk` 的宿主机资源状况（内存/磁盘）和 BuildKit builder 的超时配置。

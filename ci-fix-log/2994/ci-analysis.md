# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, EOF, euler_builder

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
Finished: FAILURE
```

### 根因定位
- 失败位置: Docker 构建步骤 `#7 [2/4]`（`RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`）
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被优雅关闭（`graceful_stop`），导致 RPC 连接中断（`EOF`）。构建器销毁后客户端无法继续与 builder 通信，确认 "no builder found"。构建当时处于 `dnf install` 下载 OS 元数据阶段（38.59s 处），与 Dockerfile 内容本身无关。

### 与 PR 变更的关联
**无关。** PR 仅新增了一个 Dockerfile（`Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`）及配套的 README.md、image-info.yml、meta.yml 元数据更新。Dockerfile 语法正确，失败发生在基础设施层（BuildKit builder 进程异常终止），属于 CI 平台侧的瞬时故障，与本次 PR 的任何代码变更均无关联。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 BuildKit 构建器实例在构建中途被异常终止的瞬时基础设施问题，非代码缺陷导致。正常情况下重新触发构建即可通过。若有条件，可检查 CI 平台 `euler_builder_*` 实例的 lifecycle 管理策略，确认是否存在对长时间运行 builder 的自动回收机制导致误杀。

## 需要进一步确认的点
- 若重试后仍然在相同阶段失败，需检查 CI 平台的 `euler_builder_*` 构建器实例是否被资源配额或超时策略自动回收。
- 确认 `ecs-build-docker-x86-hk` runner 节点在构建时段是否存在资源压力或维护事件。

## 修复验证要求
无需修复验证。该失败与 PR 代码无关，属 infra-error，Code Fixer 无需处理。

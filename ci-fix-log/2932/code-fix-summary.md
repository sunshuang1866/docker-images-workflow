# 修复摘要

## 修复的问题
CI 失败为 BuildKit 守护进程基础设施瞬时故障（infra-error），与 PR 代码无关，无需修改任何源代码。

## 修改的文件
无。此错误为 `infra-error`，不涉及代码修改。

## 修复逻辑
CI 日志显示错误发生在 BuildKit 初始化阶段：`ERROR: Error response from daemon: Could not find the file / in container buildx_buildkit_euler_builder_20260709_2057000`。此时 Docker buildx 尚未开始解析 Dockerfile 或执行任何构建步骤，属于构建节点（`ecs-build-docker-x86-hk`）上 Docker 守护进程的瞬时故障。PR 新增的文件（`Others/glibc/2.42/24.03-lts-sp4/Dockerfile` 及相关元数据文件）均未被实际执行。CI 预检（规范校验）也已通过。

**建议操作**：触发 CI 重新运行即可，极大概率会通过。

## 潜在风险
无。如果重试后同一构建节点持续复现相同错误，需检查该节点 Docker daemon 状态（磁盘空间、文件系统健康状态、BuildKit 缓存），此类排查需 CI 基础设施管理员操作。
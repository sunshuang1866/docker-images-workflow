# 修复摘要

## 修复的问题
**infra-error**：CI runner `ecs-build-docker-x86-hk` 上的 Docker buildx builder 容器启动失败（`Could not find the file / in container`），与 PR 代码变更无关。无需代码修改。

## 修改的文件
无。此故障为 CI 基础设施问题，不涉及源码改动。

## 修复逻辑
CI 在 `[internal] booting buildkit` 阶段即崩溃，Docker buildx builder 容器（`buildx_buildkit_euler_builder_*`）创建后无法访问根文件系统。此时尚未进入 Dockerfile 构建流程，任何 Dockerfile 在该 runner 上都会以相同方式失败。PR 仅新增了 `Others/glibc/2.42/24.03-lts-sp4/Dockerfile` 及文档文件，与故障无关。

建议运维在 runner 上执行以下操作后重新触发 CI：
- `docker buildx rm euler_builder_*` 清理残留 builder
- 或 `systemctl restart docker` 重启 Docker daemon

## 潜在风险
无
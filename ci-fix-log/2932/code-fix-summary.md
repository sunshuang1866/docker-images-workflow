# 修复摘要

## 修复的问题
CI 基础设施故障（BuildKit 容器启动失败），无需代码修改。

## 修改的文件
无（infra-error，不涉及代码变更）

## 修复逻辑
CI 失败发生在 `[internal] booting buildkit` 阶段，错误为 `Error response from daemon: Could not find the file / in container`。这是 Docker daemon 在启动 BuildKit builder 容器时无法找到容器根文件系统所致，属于 CI runner `ecs-build-docker-x86-hk` 上的 Docker daemon / containerd / storage driver 状态异常。

CI image specification check 已通过，证明 PR 新增的 Dockerfile 及元数据文件（README.md、image-info.yml、meta.yml）格式均正确无误。该新增 Dockerfile 结构与同目录下已有的 `24.03-lts-sp1`、`24.03-lts-sp2` 版本一致，代码无问题。

应执行 CI 侧操作（清理 BuildKit 残留容器/镜像、检查 Docker daemon 状态、重启后重新触发 CI），而非修改任何代码。

## 潜在风险
无
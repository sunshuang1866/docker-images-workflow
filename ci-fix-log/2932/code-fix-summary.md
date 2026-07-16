# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：Docker daemon 在创建 buildx BuildKit 容器后无法找到容器的根文件系统（`Could not find the file / in container`），属于 Docker 存储驱动或 daemon 运行时临时故障，与 PR 变更的 Dockerfile 及元数据文件无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 BuildKit booting 阶段（Dockerfile 中任何 `RUN` 指令执行之前），且 CI 日志的镜像规格校验（image specification check）已通过。PR #2932 仅在 `Others/glibc/` 下新增 openEuler 24.03-LTS-SP4 的 Dockerfile 和相关元数据文件，全部为标准操作。该错误极大概率为 Docker daemon 的临时性故障（存储驱动竞态、overlay2 层挂载失败），重试 CI 流水线大概率可消除。

## 潜在风险
无
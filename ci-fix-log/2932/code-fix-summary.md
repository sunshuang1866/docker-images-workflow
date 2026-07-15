# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error）：Docker BuildKit 容器启动时发生瞬态故障（`Could not find the file / in container`），与 PR 代码变更无关。

## 修改的文件
无。此失败不需要修改任何源代码文件。

## 修复逻辑
CI 分析报告明确指出：失败发生在 BuildKit 引导阶段（`[internal] booting buildkit`），此时尚未开始解析或执行任何 Dockerfile 指令。PR 新增的 4 个文件（`Others/glibc/2.42/24.03-lts-sp4/Dockerfile`、`Others/glibc/README.md`、`Others/glibc/doc/image-info.yml`、`Others/glibc/meta.yml`）没有机会被读取或执行。

错误信息 `Could not find the file / in container` 是 Docker 守护进程/overlay2 存储驱动的瞬态故障，可能原因包括 CI runner 磁盘 I/O 延迟或 BuildKit 容器根文件系统未及时就绪。

**建议操作**：重新触发 CI 流水线（重试 CI Job）。若多次重试仍失败，需检查 CI runner（`ecs-build-docker-x86-hk`）的 Docker/ BuildKit 版本及 overlay2 存储驱动健康状态。

## 潜在风险
无。
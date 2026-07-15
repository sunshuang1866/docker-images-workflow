# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（Docker BuildKit 在 `ecs-build-docker-x86-hk` runner 上引导失败），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告判定失败类型为 `infra-error`，根因是 Docker 守护进程在创建 BuildKit 构建容器后无法访问其根文件系统（`Could not find the file / in container`），错误发生在 `[internal] booting buildkit` 阶段，早于任何 Dockerfile 指令执行。该 PR 仅新增了 glibc 2.42 在 openEuler 24.03-LTS-SP4 上的标准模板文件，不涉及任何可能导致此类错误的代码变更。

建议操作：重新触发 CI 运行（retry），大概率可自行恢复。若持续复现，需排查 runner 节点的 Docker 存储驱动状态或磁盘空间。

## 潜在风险
无
# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告确认该失败为 BuildKit 构建器实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被优雅关闭（`graceful_stop`），导致 RPC 连接中断。PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套的 README.md、image-info.yml、meta.yml 更新，Dockerfile 语法正确，失败发生在基础设施层，属于 CI 平台侧的瞬时故障，与本次 PR 的任何代码变更均无关联。

**修复方式**: 重新触发 CI 构建即可。

## 潜在风险
无
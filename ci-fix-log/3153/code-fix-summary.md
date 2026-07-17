# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。CI 的 appstore 发布预检工具错误地将根目录文档文件 `README.md` 纳入镜像路径规范校验范围，导致路径检查失败。

## 修改的文件
无（无需修改任何代码）

## 修复逻辑
根据 CI 失败分析报告，本次失败类型为 `infra-error`，根因是 CI 工具 `eulerpublisher/update/container/app/update.py` 的 appstore 路径校验逻辑过于激进，将所有被修改的文件（包括根目录项目级文档）都纳入 appstore 镜像条目路径规范检查。PR #3153 仅修改了根目录的 `README.md`，属于纯文档更新，不涉及任何 Dockerfile、镜像构建或发布逻辑。该问题与 PR 代码变更无关，应由 CI 团队在 `update.py` 中增加过滤逻辑（排除非镜像路径下的文件）来解决，而非修改 PR 中的文件。

## 潜在风险
无（未修改任何代码）
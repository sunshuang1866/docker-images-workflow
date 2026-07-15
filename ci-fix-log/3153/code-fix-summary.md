# 修复摘要

## 修复的问题
无需代码修复——CI 失败属于基础设施问题（infra-error），由 eulerpublisher 工具将根级纯文档文件 `README.md` 错误纳入 appstore 镜像路径校验导致。

## 修改的文件
无（无需对仓库文件做任何修改）

## 修复逻辑
1. PR #3153 仅修改了根级文档 `README.md` 和 `README.en.md`，用于更新基础镜像可用 Tags 列表，不涉及任何应用镜像 Dockerfile、meta.yml、image-list.yml 等构建相关文件。
2. CI 工具 eulerpublisher 的 appstore 发布规范检查将所有变更文件无差别纳入镜像路径校验流程，工具要求路径以 `/` 开头（期望 `/README.md`），而 diff 输出的相对路径 `README.md` 不满足该格式约束，导致误报 FAILURE。
3. CI 失败分析报告明确结论：失败类型为 `infra-error`，与 PR 代码变更无关，应由 CI 团队在 eulerpublisher 工具侧修复——为 appstore 路径校验添加根级文档文件白名单过滤，或在 trigger 层对纯文档 PR 跳过该检查。

## 潜在风险
无（未修改任何代码，不对仓库产生任何影响）
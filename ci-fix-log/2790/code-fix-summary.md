# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施误报（infra-error），与 PR 变更内容无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：失败类型为 `infra-error`，根因是 appstore 规范检查工具 `eulerpublisher/update/container/app/update.py` 对仓库根目录的 README 文档文件（`README.md`、`README.en.md`）进行了不当的路径校验，属于 CI 基础设施自身的缺陷。本次 PR 仅修改了两个 README 文件中的镜像 Tags 列表（24.03-lts-sp2 → 24.03-lts-sp3 等），属于纯文档内容更新，任何修改根目录 README 的 PR 都会触发相同误报。因此源代码无需且不应做任何修改。

## 潜在风险
无
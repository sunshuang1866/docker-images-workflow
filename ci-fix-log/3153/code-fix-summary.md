# 修复摘要

## 修复的问题
无需代码修改。CI 失败是 appstore 发布规范预检对纯文档 PR 的误报（infra-error）。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了仓库根目录的 `README.md`，更新基础镜像可用 tag 列表，属于纯文档变更。CI 的 appstore 发布规范预检 (`eulerpublisher/update/container/app/update.py`) 在扫描变更文件时，检测到根路径的 `README.md` 不在 appstore 镜像发布目录（如 `AI/`、`Bigdata/` 等）中，触发了 `[Path Error]`。

分析报告明确指出：此错误与 PR 变更内容无关，是 CI 流程对纯文档 PR 的过度检查导致的误报。README.md 的变更内容本身正确无误，不需要任何代码层面的修复。需要调整的是 CI 流水线中 appstore 预检逻辑，使其对仅涉及根级文档文件（`README.md`、`README.en.md`）的 PR 跳过路径校验。

## 潜在风险
无
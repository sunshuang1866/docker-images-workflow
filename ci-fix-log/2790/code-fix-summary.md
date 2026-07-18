# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）：PR #2790 仅修改了根级文档文件 `README.md` 和 `README.en.md`，属于纯文档更新，不涉及任何 Docker 镜像提交。但 CI 流水线的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）对所有 PR 变更文件执行路径校验，根级文档文件无法映射到合法的 Docker 镜像目录结构，导致误报 `[Path Error] The expected path should be /README.md`。**无需代码修改。**

## 修改的文件
无。本次 CI 失败属于基础设施层面问题，PR 中的 `README.md` 文件内容本身正确无误，不需要修改。

## 修复逻辑
根据 CI 失败分析报告，失败类型为 `infra-error`（置信度：高）。根因是 CI 流水线对纯文档 PR 也执行了 appstore 发布规范检查，而该检查预期变更文件应属于某个 Docker 镜像的最小目录单元（如 `{category}/{image}/{version}/{os-version}/...`），根级 `README.md` 和 `README.en.md` 不符合此预期。真正的修复应在 CI 流水线配置或 `update.py` 中增加对根级文档文件的豁免/跳过逻辑，但这超出了本 PR 的代码变更范围（`pr.changed_files` 仅包含 `README.md`）。

## 潜在风险
无。未对任何文件进行代码修改，不会引入新问题。建议 CI 团队在流水线配置中为纯文档 PR 增加 appstore 检查跳过规则。
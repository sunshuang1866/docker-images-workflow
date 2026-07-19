# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error），由 appstore 发布规范检查工具对纯文档 PR 的路径格式校验过严导致，与 PR 改动的 README.md 内容无关。

## 修改的文件
无（PR #2790 仅涉及 `README.md` 的文档内容更新，`README.md` 本身无代码质量问题，无需修改）

## 修复逻辑
CI 分析报告明确指出：PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（纯文档标签列表更新），但 CI 的 appstore 发布规范检查工具对所有变更文件执行路径格式校验，将 git diff 输出的无前导斜杠路径 `README.md` 与期望的带前导斜杠路径 `/README.md` 进行严格字符串比较，导致不匹配判定为 FAILURE。此根级文档变更不应被纳入应用镜像提交规范检查范围，属于 CI 基础设施问题，与 PR 改动内容无关。

根本修复需要在 CI 编排工具（`eulerpublisher/update/container/app/update.py`）中对根级 README.md/README.en.md 文件进行豁免处理，或对纯文档类 PR 跳过 appstore 发布规范检查步骤。这些变更不在 PR 涉及的文件范围（`pr.changed_files: ['README.md']`）内。

## 潜在风险
无
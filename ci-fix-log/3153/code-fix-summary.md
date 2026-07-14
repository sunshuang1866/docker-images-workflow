# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）错误地对仓库根级文档文件 `README.md` 和 `README.en.md` 执行了应用镜像路径校验，导致纯文档修改的 PR 被阻断。这是一个 CI 基础设施问题（infra-error），PR 中的 README 文件内容本身无误，无需代码修改。

## 修改的文件
无。PR 的变更文件（`README.md`、`README.en.md`）内容正确，无需修改。

## 修复逻辑
分析报告指出失败根因在 CI 的 `update.py:273` 路径校验逻辑。该预检工具的职责是校验 appstore 应用镜像目录下文件的路径规范性，但它错误地将仓库根级的纯文档文件（`README.md`、`README.en.md`）也纳入了校验范围，导致两者均被判定为路径错误（即便 `README.md` 与实际预期路径 `/README.md` 一致也被标记为 FAILURE）。正确的修复应在上游 CI 工具 `eulerpublisher` 的 `update.py` 中实现：将路径校验范围限定在应用镜像目录内，对仓库根级文档文件予以跳过或加入白名单。受限于本 PR 只允许修改 `README.md` 和 `README.en.md`，无法触及 CI 工具代码。

## 潜在风险
无。README 文件内容未经修改，不存在引入新问题的风险。
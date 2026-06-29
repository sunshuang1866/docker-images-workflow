# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范校验（`eulerpublisher/update/container/app/update.py:273`）错误地将仓库根目录的 `README.md` / `README.en.md` 纳入镜像发布路径检查，导致合法文档更新的 PR 被拦截。无需对 PR 允许修改的文件进行代码变更。

## 修改的文件
无代码修改。

## 修复逻辑
PR #2790 仅更新了仓库根目录的两个 README 文件中的 Tag 列表（新增 `25.09`、更新 `24.03-lts-sp3` 为 latest），属于合法的仓库级文档维护。CI 的 appstore 发布规范校验逻辑未区分"仓库级文档"和"镜像级文档"，将根目录 README 文件也按镜像发布路径规则（如 `<image>/README.md`）校验，导致路径错误误报。

真正需要修复的是 CI 校验工具 `eulerpublisher/update/container/app/update.py` 的路径检查逻辑——应在扫描 PR diff 文件时排除仓库根目录下的非镜像文件（如 `README.md`、`README.en.md`、`.gitignore` 等），或在校验前过滤掉不位于镜像子目录内的文件。该文件不在 PR 允许修改的文件列表（`['README.en.md', 'README.md']`）中，无法在此 fix 分支中修复。

**结论**：此为 CI 基础设施问题（infra-error），PR 内容本身合法，无需对 README 文件做任何修改。

## 潜在风险
无——未对仓库代码做任何修改，不引入任何回归风险。建议在 CI 校验工具中增加根目录非镜像文件的过滤逻辑，避免未来类似仓库文档 PR 被误拦截。
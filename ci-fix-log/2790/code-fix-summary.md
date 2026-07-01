# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**，由 CI 工具 `eulerpublisher/update/container/app/update.py` 的 appstore 路径校验逻辑导致，与企业仓库代码无关。

## 修改的文件
无。PR #2790 改动的 `README.md` 和 `README.en.md` 内容正确（仅更新可用镜像 Tags 列表），无需修改。

## 修复逻辑
CI 失败根因：`update.py:273` 的 appstore 发布规范预检器未区分「仓库根目录的项目级 README」与「具体镜像目录的 appstore README」，将所有被修改的 README 文件无差别纳入 appstore 路径检查。`README.md` 和 `README.en.md` 位于仓库根目录，不隶属于任何镜像目录，不应受镜像路径规范 `{category}/{image-name}/.../README.md` 约束。

修复应在 CI 工具 `update.py` 中增加根目录级文件豁免规则，而非修改本仓库代码。由于 `update.py` 不在 PR 变更文件列表 `['README.en.md', 'README.md']` 中，且本仓库代码本身无缺陷，不做代码修改。

## 潜在风险
无。本仓库代码无需任何改动，风险在于 CI 基础设施侧 `update.py` 需独立修复以豁免根目录级文档文件。
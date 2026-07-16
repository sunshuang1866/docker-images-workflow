# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范预检工具 (`update.py`) 对根级 `README.md` 路径校验存在 bug，将正确的路径 `README.md` 报告为 `[Path Error] The expected path should be /README.md`。PR 仅修改文档内容，不涉及镜像发布，该检查为误报。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败类型为 **infra-error**（CI 基础设施问题），非 PR 引入的代码缺陷。根因在 `eulerpublisher/update/container/app/update.py` 的路径归一化逻辑——`git diff --name-only` 返回不带前导 `/` 的相对路径（如 `README.md`），而校验逻辑期望绝对路径（如 `/README.md`），导致根级文件始终无法通过校验。同时该工具未过滤纯文档类 PR，对不涉及镜像发布变更的 PR 也执行了不必要检查。

`README.md` 内容本身正确，位于仓库根目录，路径合法。应修复 `update.py`（不在本 PR 变更范围内）中的路径比较逻辑和检查范围过滤。

## 潜在风险
无——未对任何源文件做修改。
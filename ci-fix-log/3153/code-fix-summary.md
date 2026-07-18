# 修复摘要

## 修复的问题
CI 基础设施误报，无需代码修改。

## 修改的文件
无（本次 CI 失败为 infra-error，不属于 PR 代码问题）。

## 修复逻辑
CI appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py:273`）对 PR 中修改的 `README.md` 进行了路径校验，判定其"路径错误（期望路径为 `/README.md`）"。但 PR #3153 仅修改了仓库根级的 `README.md`（更新基础镜像可用 tags 列表），这是纯文档变更，不属于任何应用镜像目录下的文件。根级 `README.md` 不应被 appstore 路径校验规则所覆盖，此失败是 CI 工具的误报，属于基础设施问题（infra-error）。

`update.py` 位于 eulerpublisher 仓库，不在本 PR 的 `changed_files` 范围内，且本次 PR 的 `README.md` 修改内容本身正确无误，不需要也不应进行代码修改。

## 潜在风险
无。PR 的 `README.md` 变更是合法的文档内容更新，不涉及任何代码逻辑变更。
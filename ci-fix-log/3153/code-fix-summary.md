# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 `eulerpublisher` 工具的 appstore 发布规范校验逻辑缺陷引起（路径归一化缺失），与 `README.md` 的内容无关。

## 修改的文件
无。根因位于 `eulerpublisher/update/container/app/update.py:273`，该文件不在本次 PR 的 `pr.changed_files` 范围内（仅允许修改 `README.md`），且 `README.md` 内容无误。

## 修复逻辑
CI 分析报告明确指出："与 PR 变更无实质关联"。PR #3153 仅修改了根级 `README.md` 的文档内容（更新基础镜像 Tags 列表），属于纯文档修正。CI 的 `eulerpublisher` 工具在 appstore 发布规范预检时，对变更文件 `README.md` 进行路径校验，但校验逻辑中路径字符串未做归一化处理——`git diff` 输出的路径为 `README.md`（不带前导 `/`），而校验时期望路径为 `/README.md`（带前导 `/`），字符串不完全匹配导致误报。根级 README 不属于任何镜像目录下的 README，不应纳入 appstore 路径校验范围。此问题需要在 CI 工具 `eulerpublisher/update/container/app/update.py` 中修复路径比较逻辑或增加镜像目录过滤，不属于 `README.md` 层面的代码修复范围。

## 潜在风险
无。`README.md` 未做任何修改，不会引入新问题。
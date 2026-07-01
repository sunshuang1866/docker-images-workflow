# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 appstore 发布规范路径校验问题，非 PR 内容变更引入的回归，且根因在 `eulerpublisher/update/container/app/update.py` 的路径比对逻辑/白名单配置中，不在 PR 允许修改的文件范围内。

## 修改的文件
无。

## 修复逻辑
- CI 检查脚本 (`update.py:273`) 将 `README.en.md` 和 `README.md` 均标记为路径不合法。
- `README.en.md` 不在 appstore 预期根级文件白名单中，`README.md` 路径本应合法却被标记 FAILURE（疑似前导 `/` 路径比对不一致）。
- 该失败不是由本次 PR 的内容变更（更新 Tags 列表）触发，而是 CI 对已存在文件的合规性校验。
- PR 仅允许修改 `README.en.md` 和 `README.md`，其内容与路径校验无关，修改文件内容无法解决路径检查失败。
- 根因修复需在 `eulerpublisher/update/container/app/update.py` 中将 `README.en.md` 加入白名单，或校正 `README.md` 的路径比对逻辑（如处理前导 `/`），这些文件不在 PR 变更列表中，不可修改。

## 潜在风险
若强行对 README 文件内容做无意义修改（如重命名/合并文件），会偏离 PR 原始意图并引入新的合规性问题。建议由 CI 维护者修复 `update.py` 中的路径校验逻辑。
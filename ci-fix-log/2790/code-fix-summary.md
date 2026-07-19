# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），`eulerpublisher` 工具对根级 `README.md` 的 appstore 路径校验出现误报，与 PR #2790 的内容变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出该失败类型为 `infra-error`，根因是 CI 工具 `eulerpublisher/update/container/app/update.py:273` 在 appstore 发布规范预检时，对根级 `README.md` 做了错误的路径比较（可能缺少路径规范化处理如 `os.path.normpath` 或 `lstrip('/')`），导致 `[Path Error] The expected path should be /README.md` 误报。PR 仅修改了 `README.md` 和 `README.en.md` 中的文档内容（版本列表更新），未涉及任何构建逻辑或路径变更。该问题应由 CI 维护者修复 `eulerpublisher` 工具，而非修改仓库文件。

## 潜在风险
无
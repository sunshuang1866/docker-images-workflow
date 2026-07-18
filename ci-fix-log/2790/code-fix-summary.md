# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error），非 PR 内容错误引起。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出："CI 失败并非由 PR 内容错误引起，而是 CI 工具 `update.py` 在 appstore 发布规范预检阶段的路径校验逻辑对 `README.md` 的路径表示格式（有无前导 `/`）进行了严格匹配，导致误报。"

PR #2790 仅更新了 `README.md` 和 `README.en.md` 中的可用镜像 Tags 列表，属于纯文档修改，内容正确无误。真正的问题根因位于 CI 工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中 —— diff 输出路径（如 `README.md`）与工具期望的路径格式（如 `/README.md`）由于前导 `/` 的存在与否发生严格字符串匹配失败。该修复需要由 CI 维护者在 `update.py` 中增加路径归一化逻辑（统一添加或去除前导 `/` 后再比较），而非修改 PR 源文件。由于 `update.py` 不在允许修改的文件列表（`['README.md']`）中，且 `README.md` 内容无任何需要修正的问题，此 PR 的源代码无需修改。

## 潜在风险
无 — 此问题的修复不在本 PR 范围内。建议联系 CI/EulerPublisher 维护者修复 `update.py` 中的路径归一化逻辑。
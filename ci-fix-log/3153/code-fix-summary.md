# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），非 PR 引入的代码缺陷。

## 修改的文件
无。

## 修复逻辑
CI 失败根因是 `eulerpublisher/update/container/app/update.py` 中 appstore 发布规范预检工具的路径比对逻辑缺陷：git diff 输出的文件名格式为 `README.md`（无前导 `/`），而 CI 校验逻辑期望的路径格式为 `/README.md`（含前导 `/`），导致路径归一化失败而误报。PR #3153 仅修改了根级 README 文档中的镜像 Tags 列表，内容变更本身正确无误。

修复应发生在 `eulerpublisher` CI 工具中，对 diff 路径做归一化处理（统一添加或移除前导 `/`）。该文件不在 `pr.changed_files` 范围内，故本次不做代码修改。

## 潜在风险
无。README.md 的内容变更仅涉及镜像 Tags 条目的文本更新，不影响任何构建、发布或测试流程。
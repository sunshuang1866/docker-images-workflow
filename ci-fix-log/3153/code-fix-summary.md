# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 `eulerpublisher` 工具的 appstore 发布规范预检环节的路径比对逻辑缺陷导致（相对路径 `README.md` vs 绝对路径 `/README.md`），属于 CI 基础设施问题（infra-error），非 PR 文档变更本身引入。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败根因在 `eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑，diff 输出的相对路径格式（`README.md`）与工具内部期望的绝对路径格式（`/README.md`）不一致导致误判。PR #3153 仅修改了 `README.md` 和 `README.en.md` 的基础镜像 tags 列表，为纯文档变更，内容本身完全正确。此问题需要在 `eulerpublisher` 工具中对路径做归一化处理（如统一添加或去除前导 `/`），不在 PR 代码可修改范围内。

## 潜在风险
无（未做任何代码修改）
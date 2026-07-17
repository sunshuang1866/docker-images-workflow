# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施问题（infra-error）：appstore 规范预检工具的路径校验逻辑存在缺陷，差异检测结果中的相对路径 `README.md` 与校验规则中的期望路径 `/README.md` 格式不匹配，导致误报 FAILURE。

## 修改的文件
无。PR 仅修改了 `README.md` 的内容（新增镜像 Tag 条目），文件路径正确，内容变更合法，无需对源代码做任何修改。

## 修复逻辑
CI 失败分析报告明确指出：**失败并非 PR 代码错误导致**。根因在 CI 工具 `eulerpublisher/update/container/app/update.py:273` 的路径比对逻辑中，`Difference` 列表给出的路径为 `README.md`（无前导 `/`），而校验规则期望的路径为 `/README.md`（含前导 `/`），两者格式不一致导致路径检查报 FAILURE。这是 CI 工具的 bug，需要在该 CI 工具的 `update.py` 中统一路径表示格式（统一加或去掉 `/` 前缀）。PR 源代码（`README.md`）本身无需且无法通过修改来解决此问题。

## 潜在风险
无 — 未对源代码做任何修改。
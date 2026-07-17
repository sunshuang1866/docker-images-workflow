# 修复摘要

## 修复的问题
无需代码修改 - 本次 CI 失败为基础设施误报（infra-error），与 PR 文档变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告指出，`eulerpublisher/update/container/app/update.py`（appstore 发布规范预检工具）在比对变更文件路径时，将 git diff 产出的路径 `README.md`（不带前导 `/`）与规范路径 `/README.md`（带前导 `/`）进行比对，因格式不一致导致误报。本 PR 仅修改了 `README.md` 的文档内容（更新支持的 Tags 列表），没有任何代码或构建脚本改动。该问题属于 CI 基础设施中预检工具的路径格式处理缺陷，不应通过修改本仓库的 `README.md` 来绕过。

## 潜在风险
无（未做任何代码修改）
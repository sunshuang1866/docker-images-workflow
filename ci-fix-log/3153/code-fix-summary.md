# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）：appstore 发布规范预检工具将根目录文档文件 `README.md` 和 `README.en.md` 误判为路径错误，与 PR 代码变更无关。

## 修改的文件
无。此 CI 失败为基础设施问题，不需要对 PR 代码进行任何修改。

## 修复逻辑
PR #3153 仅修改了两个根目录文档文件（`README.en.md` 和 `README.md`），更新可用基础镜像的 tag 列表。CI 流水线中的 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检逻辑将根目录下的文档文件纳入了镜像路径规范校验范围，但这些文件不属于任何应用镜像的目录结构，因此被误报为 [Path Error]。这是 CI 检查器自身逻辑缺陷，非 PR 代码问题，应由 CI 平台维护人员修复 `update.py` 中的文件过滤规则。

## 潜在风险
无
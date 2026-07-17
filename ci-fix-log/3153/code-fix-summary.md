# 修复摘要

## 修复的问题
无需代码修改 — CI 失败是基础设施问题（`eulerpublisher` 工具误将根级 README.md 纳入 appstore 路径校验），与 PR 改动内容无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认此失败属于 **infra-error**。`eulerpublisher` 工具在扫描变更文件时，对根级文档文件 `README.md` 错误地执行了 appstore 发布路径规范检查（该工具预期 appstore 变更应遵循 `{scenario}/{image}/{version}/{os-version}/Dockerfile` 子目录结构），导致校验失败。PR #3153 仅更新了 `README.md` 中可用镜像 tag 列表，不涉及任何 Dockerfile 或应用镜像目录，其内容本身正确无误。该问题需由 `eulerpublisher` 工具侧增加白名单或排除规则来修复，不在本 PR 代码范围内。

## 潜在风险
无 — 未对代码做任何修改，不存在引入新问题的风险。
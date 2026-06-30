# 修复摘要

## 修复的问题
无需代码修复。CI 失败属于 infra-error：CI 的 appstore 校验工具 `update.py` 错误地将仓库根目录的纯文档文件 `README.md` 和 `README.en.md` 纳入了应用镜像路径校验流程，导致路径格式校验失败。此问题与 PR 改动内容无关。

## 修改的文件
无。此 CI 失败不需要在 PR 侧进行任何代码修改。

## 修复逻辑
分析报告明确判定失败类型为 infra-error，根因是 CI 基础设施中 `eulerpublisher/update/container/app/update.py:273` 的 appstore 规范校验缺少对根目录纯文档文件（README.md、README.en.md 等）的过滤/白名单逻辑。修复应在 CI 工具侧完成，而非在 PR 源码中。

## 潜在风险
无
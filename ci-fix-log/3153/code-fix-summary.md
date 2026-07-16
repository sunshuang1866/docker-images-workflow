# 修复摘要

## 修复的问题
CI 基础设施误判：appstore 发布规范检查工具将根目录文档文件 `README.md` 纳入应用镜像路径校验，导致 `[Path Error]` 失败。此失败与 PR #3153 的实际代码变更无业务关联。

## 修改的文件
无。CI 分析报告将其定性为 `infra-error`，根目录 `README.md` 的文档变更不应触发 appstore 发布规范预检。无需对源代码做任何修改。

## 修复逻辑
分析报告指出：CI 的 appstore 检查工具（`eulerpublisher/update/container/app/update.py`）在校验文件变更时，将仓库根目录的 `README.md` 误认为应用镜像条目进行路径校验。根目录 `README.md` 不符合`{category}/{image-version}/{os-version}/...` 的应用镜像路径规范，导致 `[Path Error]`。

此问题属于 CI 工具层面的缺陷，需由 CI 团队修复 `update.py` 中的文件变更检测逻辑：当 PR 仅修改根级文档（如 `README.md`）而不包含应用镜像相关文件（Dockerfile、meta.yml、image-list.yml 等）时，应跳过 appstore 发布规范校验。

## 潜在风险
无（本 PR 无代码变更）。
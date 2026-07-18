# 修复摘要

## 修复的问题
无需代码修改 — 此 CI 失败为基础设施问题（infra-error），非代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定为 `infra-error`，置信度高。PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新基础镜像可用 Tags 表），属于纯文档维护操作。CI 流水线中的 appstore 发布规范预检（`eulerpublisher/update/container/app/update.py:273`）被不恰当地应用于此纯文档类 PR——该检查设计意图是验证应用镜像提交的目录结构合规性（要求 `{category}/{image}/{version}/{os}/Dockerfile` 层级），而本 PR 不包含任何应用镜像 Dockerfile 或 `image-list.yml` 变更。PR 的 README 改动本身正确且完整，CI 流水线需由维护者调整配置：对仅涉及根目录 README 文件的 PR，跳过 appstore 发布规范预检。

## 潜在风险
无 — 未对代码做任何修改。
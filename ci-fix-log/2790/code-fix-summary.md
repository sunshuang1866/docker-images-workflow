# 修复摘要

## 修复的问题
无需代码修改。CI appstore 发布规范预检脚本（`eulerpublisher/update/container/app/update.py`）对仅包含根级 README.md 变更的纯文档 PR 误触发了 appstore 目录结构校验，属于 CI 基础设施误报（infra-error）。

## 修改的文件
无

## 修复逻辑
- PR #2790 仅更新了 `README.md` 中 Tags 列表的条目（添加 `24.03-lts-sp3`、`25.09` 等），不涉及任何 Dockerfile 或应用镜像目录的新增/修改。
- 已验证新增 tag 对应的上游镜像站 URL 均可正常访问：
  - `https://repo.openeuler.org/openEuler-25.09/docker_img/` — HTTP 200，目录列表正常
  - `https://repo.openeuler.org/openEuler-24.03-LTS-SP3/docker_img/` — HTTP 200，目录列表正常
- CI 的 appstore 规范检查器检测到 `README.md` 变更后将其纳入校验流程，但根级 README.md 不属于任何 appstore 镜像目录单元（如 `AI/xxx/`），导致路径检查误报 FAILURE。
- 此 CI 流水线的 appstore 规范检查不适用于纯文档类 PR，真正的修复应在 `update.py` 的 `Difference` 检测逻辑中增加对仅含根级 README 变更 PR 的跳过逻辑。但由于该文件不在 `pr.changed_files` 列表中，且 README.md 本身内容无任何错误，本次无需对源码做任何修改。

## 潜在风险
无。README.md 内容变更正确，新增 tag 对应的上游镜像仓库均已就绪可访问。
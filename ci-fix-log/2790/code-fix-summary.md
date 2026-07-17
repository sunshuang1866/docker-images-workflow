# 修复摘要

## 修复的问题
CI 基础设施误报：appstore 发布规范预检工具错误地将仓库根目录的 `README.md` 纳入校验范围，与 PR 代码变更无关。

## 修改的文件
无。本次 CI 失败属于 infra-error，不需要对任何源文件进行代码修改。

## 修复逻辑
CI 失败直接原因为 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 路径校验逻辑误将仓库根目录的 `README.md` 纳入检查范围。PR #2790 的变更仅限于更新根目录 `README.md` 中的镜像 Tag 列表，不涉及任何 Dockerfile、meta.yml 或应用镜像目录中的文件。该错误属于 CI 基础设施/工具层面的缺陷，应由 CI 维护团队修复工具校验逻辑（如将根目录文档排除在 appstore 路径检查列表之外）。

## 潜在风险
无
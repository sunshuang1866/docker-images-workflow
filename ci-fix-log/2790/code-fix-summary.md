# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 `infra-error`（基础设施问题），由 appstore 发布规范检查器（`update.py`）对根目录项目文档 `README.md` 和 `README.en.md` 错误执行路径校验导致，与 PR #2790 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，置信度高。根因是 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 路径校验逻辑对所有变更文件（包括仓库根目录的项目文档）无条件执行路径检查，而根目录的 `README.md` 和 `README.en.md` 属于项目自身文档，不应受 appstore 应用镜像发布路径规范的约束。PR #2790 仅更新了这两个文件中的镜像 Tags 列表，属于合法的文档维护变更。

真正的修复需要修改 CI 基础设施中的 `update.py`（例如将根目录 README 加入排除列表），但该文件不在 `pr.changed_files` 允许修改的范围内，且当前工作目录不包含该文件。按照修复原则，对于 `infra-error` 不应强行修改代码。

## 潜在风险
无。此问题不涉及对 `README.en.md` 或 `README.md` 的任何修改，不影响项目文档内容。
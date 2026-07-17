# 修复摘要

## 修复的问题
无需修改代码。CI 失败由 CI 基础设施工具 `eulerpublisher/update/container/app/update.py` 错误地将仓库根目录的 `README.md` 纳入 appstore 镜像路径校验导致，并非 PR 中 `README.md` 内容有误。

## 修改的文件
- 无

## 修复逻辑
CI 分析报告明确指出："失败是由 CI 工具错误地将根目录 `README.md` 纳入 appstore 镜像发布路径校验而触发的，**并非 PR 改动内容本身有误**"。`README.md` 的修改内容（更新 supported tags 列表、新增版本条目）是正确的仓库文档更新，不应触发 appstore 镜像路径规范校验。

真正的修复需要在 `eulerpublisher/update/container/app/update.py` 中添加文件路径过滤逻辑，排除仓库根目录级别文件（如 `README.md`、`README.en.md`），使其不被纳入 appstore 发布校验。该文件不在本次 PR 的 `changed_files` 范围内，无法在此修改。

此问题本质上是 CI 基础设施逻辑缺陷，属于 infra-error 范畴。

## 潜在风险
无。`README.md` 本身无需任何代码改动。
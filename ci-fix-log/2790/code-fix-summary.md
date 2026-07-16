# 修复摘要

## 修复的问题
CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）将仓库根目录的 `README.md` 误判为应用镜像文件，对其执行了镜像级路径校验导致 `[Path Error]`。PR 本身的 README.md 变更内容正确无误。

## 修改的文件
- 无（CI 基础设施问题，不需要修改 PR 文件）

## 修复逻辑
分析报告指出该失败类型实为 CI 基础设施问题（infra-error）：失败根因是 CI appstore 预检工具在扫描 PR 变更文件时，将根目录级 `README.md` 纳入了面向应用镜像的路径格式校验流程。根目录 `README.md` 的路径 `README.md` 无法匹配镜像级路径模板 `{category}/{image}/{version}/{os-version}/README.md`，导致校验失败。

PR #2790 对 `README.md` 的修改内容（更新基础镜像 Tags 列表）本身没有代码或内容错误，无需也不应在 PR 文件中做任何修改。真正需要修复的是 CI 工具 `update.py` 中的文件过滤逻辑：在扫描 PR 变更文件时，应将仓库根目录的 `README.md` 和 `README.en.md` 排除在镜像发布规范校验范围之外。

由于 `update.py` 不在本 PR 的 `pr.changed_files` 列表中，超出本次修复范围，修复应在 CI 工具侧独立进行。

## 潜在风险
无——本 PR 的 `README.md` 文件未做任何修改，不会引入风险。
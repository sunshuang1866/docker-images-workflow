# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为基础设施问题（infra-error），非 `README.md` 内容错误导致。

## 修改的文件
无。PR 仅涉及 `README.md`，该文件内容本身无误，修改它无法解决此 CI 失败。

## 修复逻辑
CI 失败的直接原因是 appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py`）对 PR 中所有变更文件执行应用镜像路径校验时，将仓库根目录的 `README.md`（项目级文档）错误地纳入了 appstore 镜像 README 路径格式检查。根目录 `README.md` 不满足 appstore 要求的 `{category}/{image}/{version}/README.md` 路径格式，因此被标记为 FAILURE。

**真正的修复需要在 CI 工具 `update.py` 中增加文件过滤逻辑**：当变更文件路径不含场景分类目录前缀（`Bigdata/`、`AI/`、`Cloud/`、`Database/`、`HPC/`、`Storage/`、`Others/`、`Distroless/`、`Base/`）时，跳过 appstore 路径规范校验。该文件不在 `pr.changed_files` 允许修改范围内，故本次不对源码仓库做任何代码修改。

## 潜在风险
若 CI 工具暂不修改，任何对根目录 `README.md` 或 `README.en.md` 的 PR 均会重复触发此 false positive 失败。
# 修复摘要

## 修复的问题
无需代码修改 — 这是 CI 基础设施问题，非 README.md 内容缺陷。

## 修改的文件
无。本 PR 仅包含 `README.md` 的文档更新，内容合法，不存在需要修复的代码缺陷。

## 修复逻辑
CI 失败根因是 `eulerpublisher/update/container/app/update.py:273` 中的应用商店发布规范校验（appstore release specification check）对所有变更文件执行路径校验，未区分"纯文档 PR"和"应用镜像发布 PR"。根目录的 `README.md` 不匹配应用商店要求的子目录路径格式（如 `{category}/{app}/{version}/{os-version}/Dockerfile`），被误判为路径错误。

此问题需要在 CI 基础设施侧（`eulerpublisher` 仓库的 `update.py` 或 CI 流水线配置）修复，排除根目录文档文件（`README.md`、`README.en.md`）的应用商店校验，或使纯文档 PR 不触发该校验 job。当前仓库 `README.md` 无需且无法通过修改自身内容来解决此 CI 失败。

## 潜在风险
无 — 未修改任何代码。
# 修复摘要

## 修复的问题
CI 基础设施误报：`eulerpublisher` appstore 路径校验器对根级 `README.md` 变更应用了镜像目录层级校验规则，导致误报路径错误。无需修改 PR 代码。

## 修改的文件
无。PR 中 `README.md` 的内容变更（更新镜像 Tag 列表）是合法的文档维护操作，不存在代码缺陷。

## 修复逻辑
该 CI 失败属于 **infra-error**（CI 基础设施问题）。根因在 `eulerpublisher/update/container/app/update.py` 的 diff 变更过滤逻辑中，未对仓库根级文件（如 `/README.md`）做豁免处理，导致其被纳入 appstore 镜像路径规范校验。根级 README.md 是仓库门面文档，不应受应用镜像的 `{category}/{image}/{version}/{os-version}/` 层级路径约束。正确的修复方向是在 CI 工具中添加根级文件的豁免逻辑，而非修改 `README.md` 内容。

## 潜在风险
无。未修改任何代码文件。
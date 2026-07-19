# 修复摘要

## 修复的问题
无需修改代码 — CI 失败根因是基础设施工具 `eulerpublisher` 的 bug，而非 PR 变更的文件有误。

## 修改的文件
无

## 修复逻辑
CI 失败由 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检工具引起。该工具在 diff 检测中将仓库根目录的 `README.md` 视为 appstore 镜像条目进行路径校验，但根目录文档不符合 `{category}/{image-name}/{version}/{os-version}/README.md` 的层级路径格式，导致路径校验报错。

PR #2790 仅修改了 `README.md`（更新基础镜像 Tags 列表），该文件是仓库级文档，不属于任何 appstore 镜像目录（`Base/`、`AI/` 等分类目录）。`README.md` 本身内容正确无误，bug 出在 CI 工具未对根目录文件做过滤排除。

由于：
- `README.md` 是唯一允许修改的文件，且其内容没有错误；
- CI 工具 `eulerpublisher` 不在可修改文件范围内；
- 规则禁止创建新文件（如 `.ci-ignore` 配置）；

因此本次无需对源码仓库做任何代码修改。修复应在 CI 基础设施侧完成：使 `eulerpublisher` 仅对位于镜像分类目录（`Base/`、`AI/`、`Bigdata/`、`Cloud/`、`Database/`、`Distroless/`、`HPC/`、`Others/`、`Storage/`）下的文件执行 appstore 路径校验，排除根目录文档。

## 潜在风险
无（未修改任何代码）
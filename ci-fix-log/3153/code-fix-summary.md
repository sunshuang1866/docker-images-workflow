# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py`）的路径校验逻辑缺陷导致——该工具将仓库根级文件 `README.md` 误纳入镜像子目录路径规范校验，属于 CI 基础设施问题。

## 修改的文件
无。

## 修复逻辑
PR #3153 对 `README.md` 的修改内容完全正确（更新基础镜像可用 tags 列表：将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目）。CI 失败的根本原因是 `update.py:273` 的路径校验逻辑未排除根级文件，错误地对 `README.md` 应用了镜像子目录路径格式校验（预期路径格式为 `{category}/{image}/{version}/{os-version}/README.md`）。

实际修复需要在 `update.py` 中增加文件过滤逻辑，排除仓库根级非镜像文件（如 `/README.md`、`/README.en.md`、`.gitignore` 等），但该文件不在允许修改的 `pr.changed_files` 列表（`['README.md']`）中，且 `README.md` 本身无任何需要修改的问题。因此无需对源码进行代码修改。

## 潜在风险
无。`README.md` 内容未做任何变更，不影响其他功能。
# 修复摘要

## 修复的问题
无需代码修改 — CI 失败由校验工具的设计缺陷（虚假误报）导致，与 PR 的文档变更无关。

## 修改的文件
无。PR #3153 仅修改了 `README.md`（更新基础镜像可用 tag 列表），内容完全正确，无需任何修改。

## 修复逻辑
CI 失败日志显示 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范校验工具对仓库根级 `README.md` 进行了路径校验（期望 `/README.md`，但 diff 返回 `README.md`）。该校验工具本应仅针对应用镜像子目录（`AI/`、`Bigdata/` 等）内的文件进行校验，却错误地将纯文档类 PR 的变更文件纳入了校验范围。PR #3153 仅更新了根级文档中的基础镜像 tag 列表，与任何应用镜像的发布无关，校验工具的误报与 PR 变更无因果关系。

修复应在上游 CI 工具 `eulerpublisher/update/container/app/update.py` 中增加文件路径过滤逻辑：若变更文件位于仓库根目录且不涉及任何应用镜像子目录，则跳过 appstore 发布规范校验。此修复不在本 PR 的范围内。

## 潜在风险
无 — 未对代码进行任何修改。
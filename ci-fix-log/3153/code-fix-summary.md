# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`——CI 基础设施工具 `eulerpublisher` 的 appstore 路径校验逻辑对仓库根目录的 `README.md` 产生了误报。

## 修改的文件
无（无需修改任何源码文件）

## 修复逻辑
1. PR #3153 仅更新 `README.md` 中的基础镜像 Tags 列表（文档变更），不涉及任何 Dockerfile、应用镜像或 appstore 上架相关文件。
2. CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具，将 git diff 中的 `README.md` 路径与 appstore 期望路径 `/README.md` 进行严格字符串比较，产生了误报。`README.md` 位于仓库根目录，不属于应用镜像文件，不应被纳入 appstore 路径校验。
3. 该问题属于 CI 基础设施工具层面的缺陷，需在 `eulerpublisher` 仓库中修复（排除仓库根级文档文件或修正路径比较逻辑），而非在 PR 源码中修改。

## 潜在风险
无——当前 PR 无任何代码变更，`README.md` 文档内容更新正确无误。
# 修复摘要

## 修复的问题
无需代码修改 —— CI 失败为 `eulerpublisher` 工具缺陷，PR 代码本身无问题。

## 修改的文件
无

## 修复逻辑
CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）在检测到 PR 修改了仓库根目录的 `README.md` 后，将其纳入 appstore 镜像路径校验，但根目录 `README.md` 是仓库级文档而非 appstore 镜像文件，不符合 `{image-version}/{os-version}/Dockerfile` 的 appstore 路径规范，导致路径校验误报失败。此失败与 PR 的具体改动内容无关，属于 CI 基础设施（`eulerpublisher` 工具）的缺陷——该工具应对仓库根目录文件（如 `README.md`、`README.en.md`）排除在 appstore 镜像路径校验之外。

PR 代码（`README.md`）本身正确无误，无需修改。

## 潜在风险
无。此摘要不涉及任何代码修改。
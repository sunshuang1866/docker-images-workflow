# 修复摘要

## 修复的问题
CI 基础设施误报：`eulerpublisher` 的 appstore 发布规范预检工具对纯文档 PR（仅修改 `README.md`）错误地执行了镜像目录路径校验，导致 `[Path Error] The expected path should be /README.md` 误报。源码仓库无代码缺陷，无需修改 `README.md`。

## 修改的文件
无。此问题为 CI 编排工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑缺陷，不在本仓库源码范围内。

## 修复逻辑
分析报告指出 CI 失败属于 **infra-error**（CI 基础设施问题）：

- 失败位置：`eulerpublisher/update/container/app/update.py:273`（CI 编排工具）
- 根因：`update.py` 在扫描 PR diff 时未区分根目录文档文件（`README.md`）与镜像构建文件（`Dockerfile`、`meta.yml` 等），对 `README.md` 执行了 `{image}/{version}/{os-version}` 格式的路径校验，产生误报
- 本 PR 仅修改 `README.md` 中的基础镜像 Tags 列表，不涉及任何 Dockerfile 或镜像构建文件

根据修复原则，`pr.changed_files` 仅包含 `README.md`，无法修改 CI 编排工具代码，且 `README.md` 内容本身无任何错误，因此本仓库源码无需改动。

## 潜在风险
无。本修复未修改任何源码文件。CI 失败需由 CI 基础设施团队在 `eulerpublisher` 工具中修复，具体应在 `update.py` 的 diff 文件遍历阶段增加对仓库根目录文档文件（`README.md`、`README.en.md` 等）的过滤豁免。
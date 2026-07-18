# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施误报（infra-error），由 CI 预检工具 `eulerpublisher/update/container/app/update.py` 对仓库根级文件的路径校验逻辑缺陷导致。

## 修改的文件
无。`README.md` 内容正确，无需任何修改。

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`，根因是 `eulerpublisher` 工具的 `update.py` 中 appstore 发布规范路径校验逻辑仅适用于 Docker 镜像子目录结构（如 `AI/...`、`Bigdata/...` 等），无法正确处理仓库根级文件 `README.md`，产出了 `[Path Error] The expected path should be /README.md` 的误报。

PR #2790 仅修改了 `README.md` 中基础镜像的可用 Tags 列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 等条目），内容正确且符合 README 格式规范。CI 失败并非由变更内容引起，而是 CI 工具在看到 PR 中仅包含根级 README 文件变更（无任何 Docker 镜像文件变更）时产生了误报。

根据分析报告修复方向：此问题应通过修改 CI 基础设施侧 `eulerpublisher` 工具的路径校验逻辑来解决，为仓库根级文档文件（如 `README.md`、`README.en.md`）增加豁免/跳过处理。**不应对 PR 代码做任何修改。**

## 潜在风险
无。本次不涉及代码修改。
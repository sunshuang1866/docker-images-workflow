# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需修改 PR 代码。`eulerpublisher` appstore 预检工具错误地对根级文档文件 `README.md` 触发了仅适用于应用镜像目录的路径规范检查。

## 修改的文件
无代码修改。README.md 内容正确，无需变更。

## 修复逻辑
CI 失败由 `eulerpublisher` 预检工具的路径校验逻辑缺陷引起，该工具将根级 `README.md` 误判为需要遵循 `{image-version}/{os-version}/` 层级结构校验的应用镜像文件。PR #3153 仅更新了基础镜像 Tags 列表文档（将 latest 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，补充 `24.03-lts-sp3`、`25.09` 等条目），变更内容正确且不涉及任何 Dockerfile 或镜像构建逻辑。真正的修复需要在 `eulerpublisher/update/container/app/update.py` 中排除根级纯文档文件（`README.md`、`README.en.md` 等），该文件不在本次 PR 的可修改范围内。

## 潜在风险
无。README.md 内容变更正确、格式合法，与应用镜像构建逻辑完全隔离。建议 CI 流水线后续加入 `paths-ignore` 或类似机制，对仅修改根级文档文件的 PR 跳过 appstore 预检。
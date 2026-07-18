# 修复摘要

## 修复的问题
无代码修复。CI 失败为 `infra-error`——appstore 发布预检工具 `eulerpublisher` 不支持纯文档修改类 PR，将仓库根目录 `README.md` 的变更误判为需要发布到 appstore 的镜像级文件，产生 `[Path Error]` 校验失败。

## 修改的文件
无。`README.md` 内容无任何问题，不属于代码/文档缺陷。

## 修复逻辑
PR #2790 的变更仅为在根目录 `README.md` 中新增基础镜像 tag 条目（`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`），属于仓库级文档的正常更新。CI 的 `eulerpublisher/update/container/app/update.py` 预检逻辑期望 PR 变更位于 `Category/ImageName/Version/Dockerfile` 等镜像目录结构下，对根目录文档文件执行路径校验导致失败。

此问题为 CI 基础设施层面问题（需在 CI 配置中增加对纯文档 PR 的跳过机制或管理员 bypass 通道），不在 `pr.changed_files`（仅 `README.md`）可修改范围内，无法通过修改源代码解决。

## 潜在风险
无。本 PR 为纯文档修改，不引入任何功能或构建风险。
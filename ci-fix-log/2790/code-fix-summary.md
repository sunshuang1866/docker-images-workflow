# 修复摘要

## 修复的问题
无需代码修改。本 CI 失败属于 `infra-error`，根因在 CI 基础设施工具 `eulerpublisher` 的 `update/container/app/update.py` 中 appstore 规范预检逻辑存在路径格式处理缺陷——git diff 产出的文件路径不带前导 `/`（`README.md`），而校验规则期望带前导 `/`（`/README.md`），路径比较时因格式不匹配导致误报 FAILURE。

## 修改的文件
无

## 修复逻辑
PR #2790 仅修改了 `README.md` 和 `README.en.md` 两个根级文档文件的内容（更新镜像 tag 列表和 URL），属于纯文档类改动，不涉及任何 Dockerfile、构建配置或镜像元数据。CI 失败是 `eulerpublisher` 工具在 appstore 发布规范检查阶段对根级 README 文件进行了不必要的路径格式校验所致，与 PR 变更内容无关。此问题需要在 `eulerpublisher` 仓库中修复路径比较逻辑（在比较前统一 normalize 路径格式）或为纯文档 PR 跳过该检查阶段。当前 PR 的源代码无需任何修改。

## 潜在风险
无
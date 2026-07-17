# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施误报（appstore 路径校验工具对纯文档 PR 的错误拦截）

## 修改的文件
无

## 修复逻辑
CI 失败根因是 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 发布规范校验工具对 git diff 中 `README.md` 的路径格式执行了不适用于文档文件的校验，要求路径为 `/README.md` 格式，但 diff 输出为 `README.md`（无前导 `/`），导致报错。

该问题属于 CI 工具层的行为缺陷：路径校验逻辑未区分「appstore 镜像提交」（需严格的路径格式）与「仓库根级纯文档变更」。PR #3153 仅更新 README.md 中的基础镜像 tags 列表，不涉及任何 appstore 镜像提交（无 Dockerfile、meta.yml、image-info.yml），README 内容本身无任何问题。

此错误需要 CI 工具维护者在 `update.py` 中修复路径校验逻辑（对根级文档文件添加豁免，或规范化 diff 路径统一添加前导 `/`），而非在 PR 代码层面修复。

## 潜在风险
无 — 本 PR 未修改任何代码
# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error，根因是 CI 基础设施工具 `eulerpublisher/update/container/app/update.py` 中 appstore 发布规范校验的路径比较逻辑存在缺陷（相对路径 `README.md` vs 期望的绝对路径 `/README.md` 格式不匹配），与本次 PR 的文档变更无关。

## 修改的文件
无（无代码修改）

## 修复逻辑
PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，更新了可用基础镜像的 Tags 列表，属于纯文档更新。CI 失败源于 appstore 校验工具对根目录 README 文件的路径格式比对逻辑缺陷，属于 CI 基础设施层面问题，应在 CI 工具代码（`eulerpublisher`）中修复，不应通过修改 PR 代码来绕过。

## 潜在风险
无（未做任何代码修改）
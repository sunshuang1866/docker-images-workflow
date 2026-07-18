# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 `infra-error`（CI 基础设施问题），与 PR 代码变更无关。

## 修改的文件
无（未修改任何源码文件）

## 修复逻辑
CI 失败由 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布路径预检工具触发。该工具对所有 PR 变更文件强制校验应用镜像目录结构（如 `Category/ImageName/Version/OS/Dockerfile`），但 PR #3153 仅修改了仓库根目录的 `README.md`——纯文档文件，不属于任何应用镜像目录，也不遵循 appstore 路径规范，因此预检必然失败。

CI 预检工具缺少对根级文档文件（`README.md`、`README.en.md` 等）的豁免机制，导致纯文档类 PR 被误伤。该问题需由 CI 维护团队在 `update.py` 中添加白名单豁免逻辑解决（如跳过根目录下的 `README*.md` 文件），而非通过修改 PR 源码修复。

## 潜在风险
无（未修改任何代码）
# 修复摘要

## 修复的问题
CI Appstore 发布规范预检脚本对纯文档类 PR 产生误报，无需修改任何源文件。

## 修改的文件
无（本次为 infra-error，CI 基础设施误报）

## 修复逻辑
CI 分析报告明确指出该失败并非代码或配置错误，而是 CI 检查工具 `eulerpublisher/update/container/app/update.py` 对仅修改根目录 README 文件的纯文档 PR 产生的误报。PR #2790 仅更新了 `README.md` 和 `README.en.md` 中的镜像可用 Tags 列表，不涉及任何 Dockerfile、meta.yml、image-info.yml 等镜像构建文件。CI 的 Appstore 发布规范预检将根目录的纯文档变更纳入了镜像发布路径校验流程，报告 `README.en.md` 的 `.en` 后缀与预期路径 `/README.md` 不匹配，并连带标记 `README.md` 为 FAILURE。

该问题需要在 CI 触发层面修复 — 对仅修改根目录文件（非镜像目录下文件）的 PR 直接跳过 Appstore 发布规范预检步骤，或在 `update.py` 中增加文档类文件的豁免逻辑。当前 PR 的 README 文件内容正确，无需任何代码修改。

## 潜在风险
无 — 本次未修改任何源代码文件。
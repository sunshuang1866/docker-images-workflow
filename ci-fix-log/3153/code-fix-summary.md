# 修复摘要

## 修复的问题
无需源代码修改。CI 失败系 appstore 发布规范预检（`eulerpublisher/update/container/app/update.py:273`）对纯文档 PR 的根级 README 文件错误地执行了路径校验，属于 CI 基础设施配置问题。

## 修改的文件
无。`README.md` 和 `README.en.md` 的内容合法正确，无需修改。

## 修复逻辑
CI 的 appstore 预检对所有变更文件执行路径校验，要求文件位于应用镜像的标准目录结构（如 `{category}/{app}/{version}/Dockerfile`）内。PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（文档更新：新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签链接，修正 latest 指向），未涉及任何应用镜像目录变更。此检查对纯文档 PR 缺乏豁免逻辑，导致误报。

该问题的正确修复方向是：在 CI 流水线或 `update.py` 中增加对纯文档 PR 的豁免逻辑——当 diff 中仅包含仓库根级文档文件且无任何应用镜像目录变更时，跳过 appstore 路径校验。此修改不在 `pr.changed_files` 允许修改的文件范围内，需由 CI 维护团队处理。

## 潜在风险
无。此 PR 仅涉及文档更新，不引入代码或配置变更。
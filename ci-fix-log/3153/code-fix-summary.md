# 修复摘要

## 修复的问题
无需代码修改。CI 失败是基础设施问题（infra-error），由 CI 工具 `eulerpublisher/update/container/app/update.py` 中对根级 README 的路径校验逻辑缺陷导致，PR #3153 的文档变更本身没有错误。

## 修改的文件
无（infra-error，不需要修改源码）

## 修复逻辑
PR #3153 仅更新了 `README.md` 中的基础镜像可用 Tag 列表——将 `24.03-lts-sp2, 24.03, latest` 更新为 `24.03-lts-sp4, 24.03, latest`，并新增了 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 三个 Tag 条目。这是一次纯粹的文档更新，内容正确无误。

CI 失败由 appstore 发布规范预检工具 `eulerpublisher` 触发，该工具在校验 `README.md` 路径时报出 `[Path Error] The expected path should be /README.md`。由于 `/README.md` 本身就是仓库根目录下的正确路径，路径应与期望匹配，校验仍被判为 FAILURE 说明 CI 工具的路径校验逻辑存在 bug（可能将根级 README 误纳入应用镜像级别的路径规范检查）。该问题应在 CI 工具 `update.py` 中修复（增加对仓库根级 README 的豁免处理），而非在 PR 源码中修复。

## 潜在风险
无。未对源码做任何修改，不存在引入新问题的风险。
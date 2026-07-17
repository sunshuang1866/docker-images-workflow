# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）将根级 `README.md` 标记为路径错误（Path Error），导致纯文档 PR 被误判为检查失败。此问题属于 CI 基础设施问题（infra-error），无需在源码仓库中修改代码。

## 修改的文件
无。`README.md` 内容为有效的文档更新（Tags 列表维护），不存在代码 bug 需要修复。

## 修复逻辑
- 根因：CI 的 appstore 预检工具扫描 PR diff 中的所有文件，将根级 `README.md`（仓库级别文档）误认为需要符合应用镜像发布规范的制品文件。根级 README 不包含 Dockerfile、meta.yml、image-info.yml 等发布制品，不应受 appstore 路径规范约束。
- 此问题的修复需要修改 CI 编排层（Jenkins pipeline），在 appstore 预检 job 触发前增加判断逻辑：若 PR diff 中仅包含 `*.md` 文件且无 `Dockerfile`/`meta.yml`/`image-info.yml`/`image-list.yml`，则跳过 appstore 预检。
- 由于 `eulerpublisher/update/container/app/update.py` 不在 `pr.changed_files` 列表中，且仅在源码仓库层面无法解决此 CI 基础设施问题，因此不进行代码修改。

## 潜在风险
无。未对任何源码文件进行修改，不引入新风险。
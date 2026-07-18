# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error），非 PR 代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告判定此次失败类型为 `infra-error`，根因为 CI appstore 发布规范检查工具 (`eulerpublisher/update/container/app/update.py`) 对仓库根目录 `README.md` 的路径校验逻辑存在缺陷。PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新基础镜像可用 tag 列表），未修改任何 Dockerfile、image-list.yml、meta.yml 或其他镜像构建相关文件。这是纯粹的文档更新，不应触发 appstore 镜像发布规范校验。

CI 工具未能区分纯文档 PR 与涉及镜像构建的 PR，导致合法文档变更被误判为路径错误。此问题需要在 CI 工具侧修复（增加对变更文件类型的预过滤），而非在 PR 代码侧修复。PR 本身的 `README.md` 内容变更正确无误，无需回退或调整。

## 潜在风险
无 — 此 PR 的代码变更（README.md 的 tag 列表更新）本身正确且无风险。CI 失败需由基础设施团队在 `eulerpublisher` 工具中修复。
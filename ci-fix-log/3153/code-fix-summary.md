# 修复摘要

## 修复的问题
无代码修复——本 PR 的 CI 失败属于 CI 基础设施层面的误报（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了仓库根目录的 `README.md`（更新可用基础镜像 tag 列表），属于纯文档更新。CI 的 appstore 发布规范检查器（`eulerpublisher/update/container/app/update.py`）在预检阶段对所有变更文件进行了 appstore 镜像路径规范校验，将根级 `README.md` 的路径与预期路径 `/README.md` 比对后判定不通过。这是一个 CI 工具的逻辑缺陷——检查器未区分"根级非镜像文件变更"与"appstore 镜像目录变更"，对纯文档 PR 发出了误报。

**根据分析报告判定为 infra-error，无需修改任何源码文件。**

## 潜在风险
无——不存在代码修改，因此不引入任何风险。若后续需要在 CI 工具侧修复此问题，应由 eulerpublisher 维护者在检查器中增加文件类型/路径过滤逻辑，排除根级非镜像文件的路径校验。
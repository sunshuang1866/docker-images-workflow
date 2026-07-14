# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**：CI 自身的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py:273`）对仓库根目录 `README.md` 的路径校验逻辑存在缺陷（路径前导 `/` 归一化缺失），导致 `README.md` 与 `/README.md` 比较被判为 FAILURE。

## 修改的文件
无。本 PR 的代码变更（`README.md` 中的基础镜像 Tags 文档更新）正确无误，与 CI 失败无关。

## 修复逻辑
分析报告明确指出："CI 失败与 PR 代码变更无直接关联——失败原因是 CI 自身的 appstore 路径校验脚本对仓库根目录 README.md 的路径比较逻辑存在缺陷"。根据 infra-error 处理规则，不对源码仓库做任何代码修改。

CI 校验工具应在 `eulerpublisher/update/container/app/update.py` 中修复路径归一化问题，或增加过滤条件跳过仓库根目录的非 appstore 文档文件。该修复需由 CI 基础设施维护方在 eulerpublisher 仓库中完成，不在本次 PR 范围内。

## 潜在风险
无（未修改任何代码）。
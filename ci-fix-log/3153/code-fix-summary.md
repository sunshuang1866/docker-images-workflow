# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。

## 修复逻辑
CI 失败分析报告确认此失败属于 **infra-error**，根因是 CI 管线中 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范校验工具对根目录 `README.md` 存在路径判断逻辑缺陷：校验工具期望路径为 `/README.md`（带前导斜杠），但实际从 git diff 获取的路径为 `README.md`（无前导斜杠），导致误报 `Path Error`。

PR #3153 仅修改了根目录 `README.md` 中的可用镜像 Tags 列表（纯文档更新），与构建/测试/代码逻辑无关。此 CI 失败与 PR 改动内容无实质关联，属于 CI 工具侧需修复的兼容性问题。

根据分析报告的指导，PR 作者无需修改任何文件内容。修复应由 CI 维护方排查 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑，统一处理带/不带前导斜杠的路径表示，并考虑对根目录级别的纯文档文件跳过 appstore 路径检查。

## 潜在风险
无。未对任何源文件做出修改。
# 修复摘要

## 修复的问题
CI 基础设施误报（infra-error）：CI 工具 `eulerpublisher/update/container/app/update.py` 对根级文档文件 `README.md` 执行了应用镜像路径校验，判定为 `[Path Error] The expected path should be /README.md`。此错误与 PR 变更内容无关，无需修改源代码。

## 修改的文件
无。PR #2790 仅修改了仓库根级的 `README.md`（和 `README.en.md`），均为纯文档更新，内容正确，无需修复。

## 修复逻辑
分析报告明确指出失败类型为 `infra-error`，根因在于 CI 工具的预检逻辑缺少对仓库根级文档文件的过滤。`README.md` 不在任何 `image-list.yml` 声明的应用镜像目录下，CI 对其执行路径校验属于 CI 工具自身的误报。PR 中的文档变更本身是正确的，不涉及代码 bug，因此无需对源码进行任何修改。此问题需要在 CI 工具侧（`eulerpublisher/update/container/app/update.py`）增加白名单过滤规则，跳过非 `image-list.yml` 注册目录下的文件。

## 潜在风险
无
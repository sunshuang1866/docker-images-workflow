# 修复摘要

## 修复的问题
无需代码修复 — 此为 CI 基础设施误报（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认失败类型为 `infra-error`。失败原因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具对仓库根目录文档 `README.md` 进行了不合理的路径校验，报告 `[Path Error] The expected path should be /README.md`。但 `README.md` 实际就位于仓库根目录，路径完全正确。

PR #3153 仅修改了 `README.md` 的文档内容（更新基础镜像可用 Tag 列表），变更内容本身正确无误。根级文档文件不应受 appstore 发布规范约束，此为 CI 工具缺少对根级文档文件的豁免逻辑所致。

属于 CI 基础设施问题，PR 作者无需修改源代码。建议：
1. 关闭并重新打开 PR 触发重试，或
2. 联系 CI 维护方在 `eulerpublisher` 工具中增加判断逻辑：当变更文件为仓库根级文档时跳过 appstore 路径格式校验。

## 潜在风险
无 — 未对源码做任何修改。
# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），根因是 appstore 校验工具 `eulerpublisher/update/container/app/update.py` 对纯文档变更 PR 错误触发了路径规范校验。

## 修改的文件
无

## 修复逻辑

CI 失败分析报告明确指出失败类型为 `infra-error`，根因不在 PR 变更的文件中：

1. PR #3153 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，更新 openEuler 基础镜像可用 tags 列表，变更内容完全合法。
2. CI 流水线中的 appstore 校验工具检测到变更文件 `README.md` 后，对其执行了 appstore 目录路径校验（期望路径格式 `/{category}/{image}/{version}/{os-version}/...`），但 `README.md` 位于仓库根目录，不属于任何 appstore 镜像目录，导致校验误报 `Path Error`。
3. 该问题需在 CI 工具端（`update.py`）或 CI 流水线定义中增加对根目录文档文件的跳过逻辑来修复。

按照任务指令中"如果分析报告指出是 infra-error，在 output_file 中说明无需代码修改，不要强行改代码"的要求，本次不对 `README.md` 做任何修改。

## 潜在风险
在 CI 工具端修复前，任何仅涉及仓库根目录文档文件的 PR 可能会遇到同样的 appstore 校验误报。建议在 `eulerpublisher/update/container/app/update.py` 中增加文件过滤逻辑：当变更文件仅包含根目录文档（如 `README.md`、`README.en.md`、`LICENSE` 等）且无 appstore 镜像目录变更时，跳过路径校验。
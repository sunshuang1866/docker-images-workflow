# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 **infra-error**（CI 基础设施问题），非 PR 代码变更引起。

## 修改的文件
无。

## 修复逻辑

CI 分析报告明确指出本次失败为 `infra-error`：

- PR #3153 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新可用基础镜像 Tags 列表），属于纯文档变更。
- CI 失败的直接原因是 appstore 发布规范校验工具 (`eulerpublisher/update/container/app/update.py`) 在路径检查阶段未对根级文档文件做豁免处理，错误地将镜像目录结构规则（`{category}/{name}/{version}/{os}/`）应用于根级 `README.md`，导致误报 `[Path Error] The expected path should be /README.md`。
- 该问题根因在 CI 基础设施的校验脚本中，而非本仓库的 `README.md` 内容。按照修复原则，`infra-error` 无需（也不应）通过修改 PR 变更文件来修复。

## 潜在风险
无。根级 `README.md` 内容本身正确，无需修改。CI 校验工具对根级文档的误报问题需由 CI 流水线维护方在 `eulerpublisher` 仓库中修复，为 `update.py` 增加根级文档文件的路径豁免白名单。
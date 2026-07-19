# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 `eulerpublisher` appstore 校验工具对仓库根目录 `README.md` 错误触发应用镜像路径规范检查导致。

## 修改的文件
无。

## 修复逻辑
CI 分析报告明确指出失败为 appstore 校验工具误判——仓库根目录的 `README.md` 是仓库级文档，不应被纳入应用镜像发布规范检查范围。错误类型为 `[Path Error]`（期望路径 `/README.md`），与 PR 变更内容无关。PR 修改（更新镜像 Tags 列表）内容本身正确。

根据修复原则，对于 `infra-error` 类型的 CI 失败不应强行修改代码。该问题需由 CI 工具侧修复（`eulerpublisher/update/container/app/update.py` 第 273 行校验逻辑），不在本代码库文件范围内。

## 潜在风险
无。
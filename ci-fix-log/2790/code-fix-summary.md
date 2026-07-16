# 修复摘要

## 修复的问题
无需代码修改。本次 CI 失败属于基础设施错误（infra-error）：appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py`）错误地将仓库根级 `README.md` 纳入路径校验范围，产生误报 `[Path Error]`。PR #2790 仅修改了根级文档，不涉及任何应用镜像代码。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出本次失败为 infra-error，根因是 CI 检查工具对根级 README.md 的路径校验逻辑存在问题，与 PR 代码变更内容无关。PR 变更仅限于 `README.md` 的文档内容（更新可用镜像 Tags 列表和锚链接），不存在应用镜像层面的构建、测试或发布风险。由于 `pr.changed_files` 仅包含 `README.md` 且分析报告结论为"无需验证——本失败为 CI 基础设施问题"，不对任何源代码做修改。

## 潜在风险
无
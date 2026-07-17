# 修复摘要

## 修复的问题
无需代码修改 — CI 基础设施问题（infra-error）：appstore 预检工具错误地将根目录文档文件 `README.md` 纳入镜像条目路径校验流程。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认失败根因为 `eulerpublisher/update/container/app/update.py:273` 的 appstore 规范校验阶段未正确过滤根目录文档文件（如 `README.md`）。该工具对所有 diff 中的文件执行 appstore 镜像条目路径规范校验，但根目录下的 `README.md` 是项目文档而非镜像条目目录中的文件，路径格式不满足 `分类/镜像名/版本/OS版本/文件` 的层级规范，被错误判定为 "Path Error"。

PR #2790 仅修改了 `README.md` 的 Tags 列表（纯文档更新），变更内容本身正确。根因在于 CI 工具 (`update.py`) 缺少对根目录非镜像文件的白名单过滤逻辑，属于 CI 基础设施缺陷，与 PR 代码无关。

由于 `update.py` 不在 `pr.changed_files` 中（仅 `README.md`），且分析报告指向 CI 基础设施问题，按照修复原则**不强行修改代码**。

## 潜在风险
无。此结论不影响其他功能，PR 的文档更新合入后不受此 CI 检查影响（该 CI 检查为 appstore 发布规范预检，文档文件本身不参与发布流程）。
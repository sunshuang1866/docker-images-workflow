# 修复摘要

## 修复的问题
无需代码修改 — CI 失败属于 infra-error（基础设施错误），由 CI 校验工具 `eulerpublisher/update/container/app/update.py` 的路径比对逻辑缺陷导致。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：
- 失败类型为 `infra-error`
- 根因是 CI 校验工具 `update.py:273` 在比对 git diff 中的路径（格式为 `a/README.md` 或 `b/README.md`）与预期路径 `/README.md` 时，未正确剥离 `a/` / `b/` 前缀，导致字面比较失败
- 本次 PR 为纯文档变更（仅更新 `README.md` 中基础镜像可用 tag 列表），变更内容本身正确无误
- 此类问题属于 CI 基础设施层面的 bug，需要 CI 工具维护者修复 `update.py` 中的路径归一化逻辑，而非当前 PR 仓库代码层面可修复

根据工作流程约定，对 `infra-error` 不进行代码修改。

## 潜在风险
无
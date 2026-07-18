# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error）：CI 预检工具 `eulerpublisher/update/container/app/update.py` 在路径归一化时，对根目录文件生成的路径缺少前导斜杠（`README.md` vs 期望的 `/README.md`），导致 appstore 发布规范预检的路径对比不通过。

## 修改的文件
无。PR #3153 的代码变更（仅更新 README.md 中的可用镜像 Tags 列表）本身正确无误，无需修改。

## 修复逻辑
根据 CI 分析报告，该失败由 `eulerpublisher` 工具侧的路径格式化策略缺陷引起，而非由 PR 的文档内容变更导致。任何涉及根目录 `README.md` 变更的 PR 都可能触发同类失败。此问题需在 CI 工具侧修复（在 `eulerpublisher/update/container/app/update.py` 中增加路径前导斜杠的统一规范化处理，或在校验过滤逻辑中排除仓库根目录级别的通用文件），不涉及本仓库源码的改动。

## 潜在风险
无。本 PR 未做任何代码修改，仅文档内容更新，不影响任何构建逻辑、Dockerfile 或 CI 流程。
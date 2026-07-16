# 修复摘要

## 修复的问题
无需代码修改。CI 失败根因是 appstore 发布规范预检工具 (`eulerpublisher/update/container/app/update.py`) 的路径比较逻辑存在严格匹配缺陷——git diff 产出的路径 `README.md`（无前置 `/`）与 CI 工具内部期望的 `/README.md`（带前置 `/`）不匹配。该工具不在 PR 变更文件 (`README.md`) 范围内，无法通过修改源码仓库修复。

## 修改的文件
- 无（`README.md` 本身内容正确，无需修改）

## 修复逻辑
本 PR 仅修改了 `README.md` 文档文件（更新基础镜像可用 Tags 列表），不涉及任何应用镜像元数据（Dockerfile、meta.yml、image-info.yml 等）的变更。CI 失败属于基础设施问题（infra-error）：

1. **路径格式化问题**：`update.py` 在比较 diff 路径与期望路径时未做统一规范化处理，导致 `README.md` 与 `/README.md` 不匹配。
2. **触发条件问题**：纯文档变更的 PR 不应触发 appstore 发布规范预检，CI 流水线缺少跳过纯文档 PR 的机制。

应在 CI 基础设施侧修复：
- `update.py` 路径比较前统一添加/移除前置 `/` 做规范化
- 或为纯文档 PR（仅修改根目录 README）添加 appstore 预检跳过逻辑

## 潜在风险
无（未对源码仓库做任何修改）
# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：appstore 发布规范预检器（`update.py`）错误地将根目录 README 文档文件判定为 Docker 镜像目录路径不合规。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出本次失败属于 **infra-error**，根因是 CI 流水线中的 `eulerpublisher/update/container/app/update.py` 第 222–273 行路径校验逻辑未对纯文档变更 PR 做豁免处理，导致 `README.md` 和 `README.en.md` 这两个仓库根目录文件被误报为 "Path Error"。PR 自身的改动（仅更新 README 中的 openEuler 基础镜像可用标签列表）是完全正确的，不涉及任何 Docker 镜像变更，**无需对 PR 文件做任何代码修改**。

正确的修复应在 CI 配置层面进行（方向 1）：为 appstore 规范预检步骤添加文件路径过滤器，排除仓库根目录非 Docker 镜像目录下的文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md`、`.github/` 等），使纯文档 PR 不再被误报。该修复不在本 PR 的变更文件范围内，需要由 CI 团队处理。

## 潜在风险
无。未对任何源代码文件进行修改。
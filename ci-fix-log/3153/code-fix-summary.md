# 修复摘要

## 修复的问题
CI 失败为基础设施误报（infra-error），无需修改源代码。

## 修改的文件
- 无

## 修复逻辑
CI 分析报告明确指出：本次 CI 失败类型为 **infra-error**，置信度高。失败原因是 CI 流水线中的 appstore 发布规范校验工具（Eulerpublisher `update.py`）未排除仓库根目录的项目文档（`README.md`），将其错误纳入 appstore 镜像路径校验范围，导致 `Path Error`。

本 PR #3153 仅更新根目录 `README.md` 中可用基础镜像 tag 列表，属于纯粹的文档更新，不涉及任何 appstore 镜像文件的增删改。CI 失败与 PR 变更无关。

由于：
1. 失败根源在 CI 基础设施（Eulerpublisher 校验逻辑），不在本仓库源码
2. `README.md` 的内容本身没有问题，无需修改
3. 本次被修改的文件（`README.md`）不在需要修复的范围内

因此，本次无需对源码仓库进行任何代码修改。建议由 CI/基础设施团队修复 Eulerpublisher 的路径过滤逻辑，排除根级项目文档目录。

## 潜在风险
无
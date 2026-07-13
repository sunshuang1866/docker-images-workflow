# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`，根本原因是 CI 流水线的 appstore 发布规范校验器（`update.py`）将根级文档文件（`README.md`、`README.en.md`）纳入路径检查范围，产生了误报。

## 修改的文件
无（infra-error，代码仓库无需修改）

## 修复逻辑
分析报告明确指出该失败属于 `infra-error`（CI 基础设施问题），而非 PR 代码缺陷。PR #3153 仅修改了 `README.md` 和 `README.en.md` 两个根级文档文件（更新基础镜像可用 tags 列表），没有任何 Dockerfile、meta.yml 或其他镜像发布文件的变更。CI 的 `update.py` 校验器对所有变更文件执行 appstore 路径合规性检查，但根级文档文件不在任何镜像目录结构下，不适用于该检查逻辑，因此被误报为 "Path Error"。

此问题需要修改 CI 校验器 `update.py` 中的文件分类逻辑，使其在检测到变更仅涉及根级文档文件时自动跳过 appstore 发布规范检查。但这属于 CI 配置/基础设施层面的修复，不在本 PR 的代码变更范围内，也不在允许修改的文件列表中。

## 潜在风险
无
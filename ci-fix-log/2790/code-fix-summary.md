# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：`eulerpublisher` CI 预检工具对仓库根目录的 `README.md` 执行了面向 image 发布目录结构的路径校验，导致路径校验失败。该失败并非 README 内容问题，无需修改源代码。

## 修改的文件
- 无代码修改

## 修复逻辑
根据 CI 失败分析报告，PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新 Supported Tags 列表），这两个文件的内容本身正确无误。CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py:273` 处的 appstore 发布规范预检工具对该根级 README 文件执行了路径校验（期望的文件路径格式应为 `{category}/{image}/{version}/{os-version}/Dockerfile`），而根目录 README 不属于任何 image 发布路径，因而被拒绝。此问题应在 CI 工具/流水线层面处理（将根目录 README 排除在路径校验范围之外），不属于源码修复范畴。

## 潜在风险
无
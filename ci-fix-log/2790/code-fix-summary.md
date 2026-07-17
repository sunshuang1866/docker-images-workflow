# 修复摘要

## 修复的问题
无代码修改 — 该 CI 失败属于基础设施问题（infra-error），与 PR 代码质量无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出该失败类型为 `infra-error`。根因是 CI 流水线中的 appstore 发布规范校验步骤（`eulerpublisher/update/container/app/update.py:273`）对纯文档变更 PR 也执行了路径校验，将根目录 `README.md` 判定为路径错误。PR #2790 仅修改了根目录 `README.md` 和 `README.en.md`（更新基础镜像 Tags 列表），完全不涉及任何应用镜像的新增或修改。

此问题需要在 CI 流水线层面修复：在 appstore 校验步骤前增加 PR 类型判定逻辑，当 PR diff 仅包含根目录文档文件、不包含任何应用镜像目录下的文件时，跳过 appstore 发布规范校验。这不是源码层面的问题，无需修改仓库代码。

## 潜在风险
无（未修改任何代码）
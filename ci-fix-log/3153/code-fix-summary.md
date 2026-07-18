# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**（CI 基础设施问题），与 PR #3153 中 README.md 的文档变更无关。

## 修改的文件
无。当前源代码仓库中的文件无需任何修改。

## 修复逻辑
CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 发布规范预检脚本对根级文件 `README.md` 执行了路径校验，其期望的绝对路径 `/README.md` 与 `git diff` 输出的相对路径 `README.md` 不匹配，导致校验失败。

**根因不在本仓库代码中。** PR #3153 仅更新了 README.md 中基础镜像 Tags 列表的文档内容（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目），改动内容完全正确，不涉及任何应用镜像或 appstore 发布制品。CI 流水线中的 appstore 校验流程未能区分"根级项目文档变更"与"应用镜像文件变更"，错误地将 README.md 纳入 appstore 路径校验。

修复应位于 CI 编排层面（`eulerpublisher` 工具或 Jenkins pipeline 配置），需增加按文件路径过滤的机制，排除根级文件（如 `README.md`、`README.en.md`、`LICENSE`、`CONTRIBUTING.md` 等）的 appstore 路径校验。

## 潜在风险
无。本仓库代码无需修改，不涉及代码级变更风险。
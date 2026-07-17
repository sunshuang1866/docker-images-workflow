# 修复摘要

## 修复的问题
无需代码修改 — 本次 CI 失败为 `infra-error`（CI 基础设施问题）。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 **infra-error**，根因是 CI 工具 `eulerpublisher/update/container/app/update.py` 中 appstore 发布规范校验模块的路径比较逻辑存在缺陷：`git diff` 输出的文件路径 `README.md`（相对路径，不含前导 `/`）与预期路径 `/README.md`（含前导 `/`）因格式不一致导致字符串比较失败，从而误报路径错误。

PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，文件路径本身完全正确，与 PR 的具体内容变更无关。修复此问题需要修改 CI 基础设施侧的 `eulerpublisher` 工具源码，而非修改本仓库中的任何文件。

## 潜在风险
无 — 未对源码做任何修改。
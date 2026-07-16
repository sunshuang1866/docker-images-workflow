# 修复摘要

## 修复的问题
无需代码修改。CI 失败是 `eulerpublisher` 工具内部路径校验逻辑缺陷导致的误报（infra-error），与本 PR 的文档变更无关。

## 修改的文件
无。PR 仅修改了 `README.md` 更新基础镜像 tags 列表，文件内容本身没有问题。

## 修复逻辑
CI 分析报告明确指出：CI 工具 `eulerpublisher` 的 `update.py` 在 appstore 路径校验时，`git diff` 输出的相对路径 `README.md`（无前导 `/`）与校验器预期的绝对路径 `/README.md`（含前导 `/`）格式不一致，导致根目录文件被误判为"路径错误"。`README.md` 实际位于仓库根目录，路径完全正确。此问题属于 CI 基础设施/工具侧缺陷，应由基础设施团队修复 `eulerpublisher` 的路径归一化逻辑，不在本 PR 范围内。

## 潜在风险
无。本摘要未对任何源码文件做修改。
# 修复摘要

## 修复的问题
无需代码修复。该 CI 失败为 **infra-error**，根因是 CI 路径校验工具 (`eulerpublisher/update/container/app/update.py:273`) 在路径比对时，期望路径带前导 `/`（如 `/README.md`），而 git diff 输出的路径无前导斜杠（如 `README.md`），导致字符串比对不通过。与 PR 代码变更无关。

## 修改的文件
无。PR 仅修改了 `README.md` 和 `README.en.md`（更新可用镜像 Tags 列表），文件内容和位置均正确，无需任何修改。

## 修复逻辑
该失败属于 CI 基础设施问题（infra-error），需要 CI 工具维护者修复 `update.py` 中的路径归一化逻辑（统一添加或去除前导 `/`），不涉及任何源代码改动。

## 潜在风险
无
# 修复摘要

## 修复的问题
CI 失败为 infra-error，无需修改 PR 代码。

## 修改的文件
无。

## 修复逻辑
CI 失败分析报告明确指出该失败与 PR #3153 的代码变更无关。PR 仅修改了 `README.md` 中的文档内容（更新基础镜像 tag 列表和下载链接），而失败是由 CI 工具 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑 bug 引起的：`git diff --name-only` 输出的路径格式为 `README.md`（无前导 `/`），而 appstore 规范预期的路径格式为 `/README.md`（带前导 `/`），严格字符串比较导致校验失败。

此问题需要在 CI 工具 (`eulerpublisher`) 仓库中修复，分别有两种修复方向：
1. 在路径比较逻辑中对 git diff 输出添加前导 `/` 或对预期路径去除前导 `/`；
2. 将根级 `README.md` 和 `README.en.md` 加入 appstore 预检白名单。

## 潜在风险
无。本次未修改任何源代码。
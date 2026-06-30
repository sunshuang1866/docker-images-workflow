# 修复摘要

## 修复的问题
无需代码修改 — CI 失败类型为 `infra-error`，根因在 `eulerpublisher/update/container/app/update.py` 中的应用商店发布校验逻辑误报了根目录 README 文件的路径校验错误。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`（CI 基础设施问题），不是代码层面的 bug。失败的 `update.py:273` 属于 CI/发布工具链脚本，不在 PR 变更文件列表（`README.en.md`、`README.md`）内，不在允许修改范围内。PR 仅修改了仓库根目录的两个文档文件，内容本身没有问题；CI 校验工具对所有非镜像子目录内的 README 文件存在路径判断缺陷，需要由 CI 工具维护者修复 `update.py` 中的路径校验逻辑（如将根目录 README 加入白名单、修正路径比较基准）。

## 潜在风险
无（未修改任何代码）
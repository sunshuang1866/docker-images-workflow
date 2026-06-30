# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具错误地将根目录 README 文档变更判定为路径校验失败——属于 CI 基础设施流程设计问题，无需修改 PR 中的源代码文件。

## 修改的文件
- 无代码修改。`README.en.md` 和 `README.md` 内容本身没有问题（纯文档更新，新增版本 tags 条目），无需改动。

## 修复逻辑
CI 失败分析报告确认：PR 变更内容（更新根目录 `README.en.md` 和 `README.md` 中的基础镜像 tags 表格）正确无误。失败根因是 CI 流水线 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检未豁免根目录 README 文档文件，导致路径格式校验误报。正确的修复方向是在 CI 配置层面调整触发规则，使仅修改根目录文档文件的 PR 不触发 appstore 校验流水线，或在 `update.py` 中增加对根目录 README 的豁免逻辑——但这些修改不在当前 PR 允许的文件范围内，也不应由代码修复 Agent 直接操作 CI 管道文件。

## 潜在风险
无——未进行任何代码修改，不会引入新问题。
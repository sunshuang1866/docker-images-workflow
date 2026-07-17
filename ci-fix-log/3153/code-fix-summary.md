# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，由 appstore 发布规范检查工具 (`eulerpublisher/update/container/app/update.py`) 的路径比较逻辑缺陷导致。

## 修改的文件
无。PR 代码（`README.md`）无需修改。

## 修复逻辑
CI 分析报告确认：PR #3153 仅更新了根目录 `README.md` 中的基础镜像 tags 列表和链接地址，属于纯文档更新。CI 失败是由 appstore 发布规范预检工具在路径校验时，将 git diff 输出的相对路径 `README.md` 与期望的绝对路径格式 `/README.md` 进行字符串精确比较，因格式不一致而误判失败。此问题与 PR 代码内容无关，属于 CI 基础设施缺陷，需由 CI 管理员修复 `eulerpublisher` 工具中的路径归一化逻辑。

## 潜在风险
无。不涉及任何代码修改。
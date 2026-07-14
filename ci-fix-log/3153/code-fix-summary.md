# 修复摘要

## 修复的问题
CI 基础设施误报——`eulerpublisher` 的 appstore 预检器错误地将仓库根目录 `README.md` 纳入 appstore 发布规范路径校验，与 PR 变更内容无关，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，根因是 CI 工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑缺陷，未正确排除仓库根级 README 文件。PR #3153 仅修改了 `README.md` 和 `README.en.md` 中的基础镜像 Tags 列表，与 appstore 发布规范预检的路径校验逻辑之间没有因果关系。根据任务指令，infra-error 类型无需源代码修改，应由 CI 维护团队在 `eulerpublisher` 工具中增加对根级 README 文件的豁免逻辑。

## 潜在风险
无
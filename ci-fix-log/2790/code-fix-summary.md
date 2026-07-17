# 修复摘要

## 修复的问题
无需代码修改。本次 CI 失败为基础设施错误（infra-error），由 CI 工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑缺陷导致，与 PR 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告指出，`eulerpublisher` 的 appstore 发布规范预检工具在路径校验时，用 `/README.md`（带前导 `/`）与 git diff 输出的 `README.md`（不带前导 `/`）做字符串比较，两者不匹配，判定为 Path Error。这是 CI 工具本身的 bug，修复应当在 `eulerpublisher` 仓库中进行（对路径做规范化处理，如统一去除前导 `/` 后再比较），而不是修改本 PR 的文档内容。PR 仅修改了根目录的 README.md 和 README.en.md，更新了基础镜像的 Supported Tags 列表，属于正常的文档维护，不涉及任何 Dockerfile、构建逻辑或镜像制品的变更。

## 潜在风险
无
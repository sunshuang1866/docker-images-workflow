# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`——appstore 发布预检脚本对纯文档 PR 错误执行路径校验，与 PR 改动内容无关。

## 修改的文件
无。PR 仅修改 `README.md` 和 `README.en.md` 的文档内容（更新可用镜像 Tags 列表），改动本身正确无误。

## 修复逻辑
CI 流水线的 `eulerpublisher/update/container/app/update.py` 对所有 PR 统一执行 appstore 路径合规检查，要求变更文件位于 `{image-version}/{os-version}/` 目录树下。本 PR 仅涉及仓库根目录下的两份 README 文件，不包含任何 Dockerfile 或镜像配置，却因路径校验不通过而被拒绝。这是 CI 预检规则缺少对纯文档 PR 豁免机制的问题，属于 CI 基础设施缺陷，不应通过修改 PR 源代码来绕过。

## 潜在风险
无。未修改任何代码文件，不会引入新的风险。
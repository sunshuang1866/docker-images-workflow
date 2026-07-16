# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error：`eulerpublisher` 路径校验工具对根目录文档文件（`README.md`）的路径格式校验过严，误将相对路径 `README.md` 与绝对路径格式 `/README.md` 比对后判定失败。

## 修改的文件
无。PR #2790 仅修改了 `README.md` 中的可用镜像 Tags 列表内容，该文档变更是合法且正确的，不存在代码缺陷。

## 修复逻辑
CI 分析报告明确归类为 `infra-error`，根因不在项目源码中，而是 CI 编排工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑对根级文档文件的误报。由于这是纯文档更新 PR，不涉及应用镜像 Dockerfile 或配置文件，不应被 appstore 规范校验流水线拦截。修复需要在 CI 工具侧（`eulerpublisher`）或 CI 流水线触发规则中进行，不在本次代码修复范围内。

## 潜在风险
无。不涉及 PR 变更文件（`README.md`）本身的改动，不会引入任何新风险。
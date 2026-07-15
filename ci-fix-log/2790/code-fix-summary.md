# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error），无需代码修改。

## 修改的文件
无。

## 修复逻辑
CI 失败源自 `eulerpublisher/update/container/app/update.py:273` 中的 appstore 发布规范检查工具路径比较逻辑缺陷。该工具在对比被修改文件路径时，未能将根目录文件 `README.md` 与期望路径 `/README.md` 进行正确的标准化匹配，导致 `Path Error`。

此问题是 CI 检查工具层面的 bug，与 PR #2790 的具体改动内容无关——只要任何 PR 触碰了仓库根目录下的 `README.md`，无论改动内容为何，都会触发此检查失败。PR 中 `README.md` 的变更（更新镜像 Tags 列表）属于纯文档更新，无代码质量问题。

该问题需要在 `eulerpublisher` 仓库的 CI 工具侧修复路径标准化逻辑，不属于本源码仓库的修改范围。

## 潜在风险
无。未对源码仓库做任何修改。
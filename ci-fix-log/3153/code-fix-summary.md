# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**（CI 基础设施问题），非 PR 代码缺陷。

## 修改的文件
无

## 修复逻辑

CI 分析报告判定此次失败为 CI 基础设施问题（`eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具），根因如下：

- PR #3153 仅修改仓库根级 `README.md`，更新可用的基础镜像标签信息，属于纯文档修改。
- CI 的 appstore 预检工具错误地将根级 `README.md` 的变更纳入镜像发布规范校验范围，触发了路径校验失败（期望路径格式为 `/README.md`，但工具报错称路径不符合 appstore 规范）。
- 根级 `README.md` 是项目通用文档，不属于任何 appstore 镜像的最小目录单元，不应触发 appstore 发布规范检查。

该问题需要在 CI 基础设施侧的 `eulerpublisher/update/container/app/update.py` 中添加排除规则，将仓库根路径的 `README.md` 排除在 appstore 校验之外。PR 本身的改动内容（`README.md`）正确且必要，无需任何修改。

## 潜在风险
无 — PR 代码无需修改，风险在于 CI 工具可能对其他纯文档类 PR 也产生误报，建议修复 CI 工具本身的校验逻辑。
# 修复摘要

## 修复的问题
CI appstore 发布规范预检器（`update.py`）错误地拒绝了根目录纯文档文件 `README.md` 和 `README.en.md` 的变更，原因是这些文件不在任何应用镜像目录下，路径校验不通过。

## 修改的文件
无。`pr.changed_files` 中的 `README.md` 和 `README.en.md` 均为纯文档文件，其内容本身没有任何语法或格式错误。CI 失败是基础设施层面（`update.py` 路径校验逻辑）的问题，无法通过修改这两个 README 文件解决。

## 修复逻辑
这是 **CI 基础设施问题（infra-error）**，不是源代码缺陷：

- `eulerpublisher/update/container/app/update.py:273` 的路径校验逻辑要求 PR 变更文件必须归属于某个应用镜像的最小目录单元（如 `AI/`、`Bigdata/` 等），但未将仓库根目录的 `README.md` / `README.en.md` 等纯文档文件加入白名单。
- 这两个 README 文件的内容正确（仅更新支持的镜像 Tags 列表和修正错误 URL），不存在任何内容层面的错误。
- 按照"不强行改代码"原则，不对 README 文件做无意义的内容修改。

**建议的正确修复**（需 CI 维护者操作）：
1. 在 `update.py` 中将根目录 `README.md`、`README.en.md` 等文档文件加入路径校验白名单。
2. 或在仓库流程中明确："纯文档修改"可直接推送到 master 分支，无需通过 appstore PR 检查流水线。

## 潜在风险
无。此次未对任何文件进行修改，不会引入新的问题。
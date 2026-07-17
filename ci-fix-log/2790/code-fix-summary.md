# 修复摘要

## 修复的问题
无需代码修改。此失败为 **infra-error**（CI 基础设施问题）。

## 修改的文件
无

## 修复逻辑
CI 失败是由 `eulerpublisher` 工具的 appstore 发布规范预检引起的。该工具将仓库根目录的 `README.md` 误纳入 appstore 级路径规范校验（预期路径 `/README.md` vs 实际路径 `README.md` 的字符串比对失败）。

PR #2790 仅修改了 `README.md`（更新 Tags 列表条目），不涉及任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关文件。仓库根级 README 不应受 app 级路径规范约束，这属于 CI 工具 `eulerpublisher/update/container/app/update.py:273` 对变更文件作用域判断的缺陷。

修复应在 CI 基础设施侧完成（过滤掉非应用镜像目录下的文件），而非在源代码仓修改。

## 潜在风险
无
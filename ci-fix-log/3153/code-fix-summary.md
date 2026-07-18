# 修复摘要

## 修复的问题
CI 基础设施问题 — `eulerpublisher/update/container/app/update.py` 中的路径规范化逻辑缺陷：git diff 产生的 `README.md`（无前导 `/`）与工具期望的 `/README.md`（带前导 `/`）格式不匹配，导致校验失败。PR 自身的 README 内容变更没有问题。

## 修改的文件
- 无需代码修改。该失败为 CI 工具（`eulerpublisher/update/container/app/update.py:273`）的路径比对逻辑缺陷，属于 `infra-error`，不在本 PR 可修改的文件范围内。

## 修复逻辑
CI 工具在比较变更文件路径与期望路径时，未对无前导 `/` 的相对路径做归一化处理。修复应在 CI 工具的路径比对逻辑中增加 `os.path.normpath` 或前缀统一处理（如 `path.lstrip('/')`），使两边的路径格式一致。本 PR 仅修改了 `README.md` 的内容，不存在需要修正的代码缺陷。

## 潜在风险
无 — 未对任何文件进行代码修改。
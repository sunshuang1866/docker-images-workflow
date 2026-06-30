# 修复摘要

## 修复的问题
CI appstore 发布规范检查 (`update.py`) 对根级文档文件 (`README.md`, `README.en.md`) 触发路径校验失败，属于 CI 基础设施问题，无法通过修改 PR 涉及的源文件解决。

## 修改的文件
- 无。`README.md` 和 `README.en.md` 的内容本身无语法或格式错误，修改它们无法解决 CI 路径校验基础设施层面的问题。

## 修复逻辑
CI 失败根因：PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），但 CI pipeline 未区分文档类 PR 与镜像发布类 PR，统一执行了 appstore 发布规范预检。`update.py` 中的路径校验要求变更文件符合 `{category}/{image}/{version}/{os-version}/Dockerfile` 目录结构，根级 README 文件不满足此规则，因此报 `[Path Error]` 导致 `FAILURE`。

由于 `pr.changed_files` 仅包含 `README.en.md` 和 `README.md`，而实际修复需要调整 CI pipeline 触发条件或 `update.py` 中的白名单逻辑，均超出允许修改的文件范围。强行修改 README 内容无法绕过路径校验规则，属于无效修复。

**建议的修复方向**（需由 CI 管理员执行）：
1. 在 CI pipeline 中添加文档类 PR 过滤逻辑（仅变更根级 `README.md`、`README.en.md`、`LICENSE` 等文件时跳过 appstore 校验）
2. 在 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑中添加根级文档文件白名单

## 潜在风险
无。未修改任何源文件。
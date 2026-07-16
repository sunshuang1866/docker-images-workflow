# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 **infra-error**，属于 CI 基础设施问题。

## 修改的文件
无。PR 仅修改了 `README.md` 和 `README.en.md` 两个根级文档文件，变更内容本身正确，无需修改源代码。

## 修复逻辑
CI 失败分析报告明确指出：该失败是 CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）对文档 PR 过度扩展所致。PR #2790 仅更新了 `README.md` 中的基础镜像 Tags 列表（纯文档维护），不涉及任何 Dockerfile、meta.yml、image-list.yml 或镜像构建相关文件。CI 工具无法将根级文档文件映射到合法的镜像发布路径而报错，属于 CI 校验逻辑的缺陷，而非 PR 变更的问题。

**根因**：CI appstore 预检规则缺少对仓库根级文档文件（`/README.md`、`/README.en.md`、`/LICENSE` 等）的排除机制，应对 CI 工具链进行修复（在 `update.py` 中加入排除逻辑或联系 CI 团队修改校验规则），而非修改此 PR 的源代码。

## 潜在风险
无。该 PR 的代码变更（README.md 文档更新）本身正确无风险，CI 失败需由 CI 团队解决。
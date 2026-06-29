# 修复摘要

## 修复的问题
此 CI 失败属于基础设施错误（infra-error），无需对 PR 变更文件（`README.md`、`README.en.md`）进行代码修改。

## 修改的文件
无。根因不在 PR 变更的文件中。

## 修复逻辑
CI 失败由 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范路径检查触发。该工具会对所有 PR 变更文件执行路径合规校验，但根目录下的 `README.md` 和 `README.en.md` 属于纯文档文件，不在 appstore 镜像发布路径白名单中，因此被误判为 [Path Error]。

PR #2790 仅修改了根目录一级的两个 README 文件（更新 Tags 列表），不涉及任何 Dockerfile 或镜像构建相关文件。`update.py` 中的路径检查没有正确处理"纯文档 PR"的场景，属于 CI 工具的缺陷，应在 `update.py` 中增加以下逻辑之一：

1. **过滤纯文档 PR**：在 `update.py:356` 附近（已识别出 diff 文件列表 `["README.en.md", "README.md"]`），当检测到变更文件仅包含根目录下的 README/文档文件且不含 Dockerfile 或 `image-list.yml` 时，跳过路径合规校验。
2. **扩展路径白名单**：将仓库根目录的 `README.md`、`README.en.md` 等基础项目文档纳入 appstore 发布规范的合法路径白名单。

当前允许修改的文件范围（`README.md`、`README.en.md`）不包含 CI 工具代码，无法在源码层面修复此问题。后续需要在 `eulerpublisher` 仓库的 `update/container/app/update.py` 中实施上述修改。

## 潜在风险
无。README 文件内容本身正确，无需改动。风险在 CI 工具侧——若短时间不加处理，后续其他纯文档 PR 也会被同样的误判拦截。
# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error（基础设施问题），与 PR 文档内容无关。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 `eulerpublisher/update/container/app/update.py` 的 appstore 发布规范预检阶段，该工具对仓库根目录的文档文件（`README.md` 和 `README.en.md`）执行路径校验，将根目录文档路径视为不合规。此失败与 PR #3153 的内容（更新可用基础镜像 tag 列表）完全无关，属于 CI 工具对 root 级文档文件变更的路径校验策略问题。PR 仅修改了两个 README 文件，不涉及镜像发布，代码层面无需也不应做任何修改。

## 潜在风险
无。此为纯文档 PR，不涉及任何代码或构建逻辑变更。
# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error）：appstore 发布规范预检工具对纯文档类 PR 进行路径校验，产生误报。

## 修改的文件
无

## 修复逻辑
CI 失败的直接原因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检对 PR 变更文件 `README.md` 执行路径校验，判定 `[Path Error] The expected path should be /README.md`。该 PR 仅包含根目录 README 文档的内容更新（更新镜像 Tags 列表），不涉及任何 Docker 镜像构建相关文件（Dockerfile、meta.yml、image-info.yml、image-list.yml）。

`README.md` 位于仓库根目录，是本仓库（openEuler 容器镜像仓）的常规文档文件，并非 appstore 发布规范所要求的应用镜像目录结构中的 `README.md`（后者应位于 `[应用名]/README.md` 路径下）。CI 管道的 appstore 预检逻辑未区分这两种不同用途的 README.md，导致对纯文档类 PR 产生误报。

`pr.changed_files` 中仅有 `README.md`，无法通过修改该文件来解决 CI 基础设施层面的检查逻辑问题。强行修改 `README.md` 不解决根本问题，且可能破坏仓库文档的正确性。

## 潜在风险
无（未修改任何代码）
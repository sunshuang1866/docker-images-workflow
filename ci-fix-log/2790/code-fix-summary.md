# 修复摘要

## 修复的问题
CI appstore 发布规范预检（`update.py:273`）对纯文档 PR（仅修改根目录 README 文件）误报路径校验失败，属于 CI 基础设施问题，PR 文件本身无需修改。

## 修改的文件
无。`README.en.md` 和 `README.md` 内容正确，不需要修改。

## 修复逻辑
该失败是 CI 基础设施层面的问题：`eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑对所有 PR 变更文件执行路径合规检查，期望路径格式为 `{category}/{image-name}/{version}/{os-version}/Dockerfile`，但根目录 `README.md` 和 `README.en.md` 是文档文件，不属于镜像构建文件，不应参与此检查。该 PR (#2790) 仅更新了 README 中的可用镜像 Tags 列表，不涉及任何镜像构建变更，因此无需对 PR 文件做任何代码修改。正确的修复应在 CI 基础设施端（`update.py`）将根目录文档文件加入白名单放行，或对纯文档 PR 跳过 appstore 检查。

## 潜在风险
无（无代码变更）。
# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 appstore 发布规范检查工具对仓库根目录 `README.md` 变更的路径校验缺陷引起，属于 CI 基础设施问题（infra-error），而非 PR 中 `README.md` 的内容或格式错误。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了仓库根目录的 `README.md`（更新可用的基础镜像 Tags 列表），属于纯文档变更，内容格式均正确。CI 失败根因在于 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具对根目录非镜像文件（如 `/README.md`）的路径校验逻辑存在不兼容——该工具期望 README 变更仅出现在镜像子目录（如 `AI/`、`Bigdata/` 等）下，根目录文档被错误判定为路径错误。由于该 CI 工具文件不在 `pr.changed_files` 列表内，且 `README.md` 内容无需修改，修复应在 CI 工具侧调整校验规则，对根目录非镜像文件予以豁免。

## 潜在风险
无。`README.md` 未做任何修改，不会引入新问题。
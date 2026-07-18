# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error）：CI 的 appstore 发布规范校验器（`eulerpublisher/update.py`）错误地将仓库根目录的 `README.md` 纳入 appstore 镜像条目路径检查，导致路径校验失败。

## 修改的文件
无（无需修改源代码）。

## 修复逻辑
PR #2790 是纯文档更新，仅修改了根目录 `README.md` 中的基础镜像 Tags 列表，不涉及任何 Dockerfile 或镜像构建文件。`README.md` 作为仓库级文档，不属于 appstore 镜像条目的目录结构，不应被 appstore 规范校验器检查。该问题是 CI 校验规则与文档类 PR 的兼容性问题，而非源代码错误。

修复方向：需联系 CI 维护方，在 `eulerpublisher/update/container/app/update.py` 中将仓库根目录的 `README.md` 和 `README.en.md` 加入 appstore 规范校验的排除列表/白名单，使其不再被当作镜像条目文件进行路径校验。

## 潜在风险
无。未对任何源代码进行修改，不存在引入新问题的风险。
# 修复摘要

## 修复的问题
CI appstore 路径校验误报：PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新基础镜像可用 tags 列表），属于仓库级文档更新，但 CI 脚本 `eulerpublisher/update/container/app/update.py` 的 appstore 路径校验逻辑将这两个根目录 README 文件误判为应用镜像目录下的文件，要求其符合 `{app}/{version}/{os-version}/README.md` 的结构，导致虚假失败。

## 修改的文件
无需修改 `pr.changed_files` 中的文件。`README.md` 和 `README.en.md` 的文档内容更新（更新基础镜像 tags 列表）完全合法且正确，不存在代码或内容错误。

## 修复逻辑
- **根因**：CI 的 appstore 发布规范预检脚本对所有 PR 变更文件执行应用镜像路径校验，未区分仓库级文档（如根目录 README）与应用镜像文档（如 `{app}/{version}/{os-version}/README.md`）。本 PR 的变更仅涉及根目录文档，不隶属于任何应用镜像目录，被校验脚本误判。
- **判定**：此问题属于 CI 基础设施（infra-error）——PR 改动本身正确无误，CI 验证逻辑存在缺陷。真正的修复应在 `eulerpublisher/update/container/app/update.py` 中增加路径过滤，排除仓库根目录和非应用镜像路径下的文件（如 `README.md`、`README.en.md`、`.github/` 下的文件等）。
- **无需代码修改**：原始 PR 只涉及两个 README 文件的内容更新，这些文件内容正确，不是 CI 失败的根源。`update.py` 不在 `pr.changed_files` 列表内，不属于可修改范围。

## 潜在风险
无。PR 的 README 变更是合法的文档更新，不涉及任何代码逻辑变更，强行修改 README 文件也无法解决 CI 校验脚本的缺陷。
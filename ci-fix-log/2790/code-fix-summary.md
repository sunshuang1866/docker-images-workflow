# 修复摘要

## 修复的问题
CI appstore 发布规范校验工具（`eulerpublisher/update/container/app/update.py`）对仓库根目录 `README.md` 执行了 appstore 镜像发布规范检查，触发 `[Path Error]` 误报。该文件是仓库文档索引，并非应用镜像的发布定义文件，不应被 appstore 规范校验。

## 修改的文件
- `README.md`: 未做代码修改

## 修复逻辑
该 CI 失败是 **CI 基础设施配置问题**，而非 `README.md` 内容错误。根因在 `eulerpublisher/update/container/app/update.py` 的校验逻辑：该工具对所有 PR 变更文件无差别执行 appstore 发布规范检查，而未区分根目录文档文件和实际应用镜像目录下的文件。根 `README.md` 本质是面向用户的仓库文档索引（包含 Tags 列表、目录结构说明等），不包含 appstore 要求的 `Dockerfile`、`meta.yml`、`image-info.yml` 等结构，校验失败属于误报。

由于 `eulerpublisher/update/container/app/update.py` 不在原始 PR 的变更文件列表中（`['README.md']`），且该错误与 `README.md` 的内容无关（错误类型为 `[Path Error]`，针对文件路径/结构调整），无法通过修改 `README.md` 解决。正确的修复方向是：在 CI 校验工具中增加对仓库根目录纯文档文件的跳过逻辑，或配置 CI pipeline 在仅变更文档文件时跳过 appstore 检查。

## 潜在风险
无。`README.md` 未做任何修改，不影响现有功能。
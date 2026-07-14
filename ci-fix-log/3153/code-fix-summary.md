# 修复摘要

## 修复的问题
无代码修改。CI 失败属于基础设施误报（infra-error），根级 README 文档文件被 appstore 发布规范预检误判为路径错误。

## 修改的文件
无

## 修复逻辑
PR #3153 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，这两个文件是仓库级别的文档文件，不属于任何应用镜像目录结构（`{app_category}/{app_name}/`）。CI 流水线中的 appstore 发布规范预检脚本 `eulerpublisher/update/container/app/update.py` 对所有变更文件进行路径校验时，未区分根级文档文件与应用镜像文件，导致误报 FAILURE。

该问题根因在 CI 预检脚本逻辑缺陷，而非 README 文件内容或 PR 变更本身。PR 中 README 文件的内容变更（更新可用镜像 Tags 列表）是正确的。此类纯文档类 PR 不应执行 appstore 路径校验，需要在 CI 脚本中增加对根目录文档文件的豁免机制，或调整流水线配置使纯文档 PR 跳过该预检步骤。

由于 `update.py` 不在 `pr.changed_files` 列表中，且 README 文件本身无需修改，本次不进行任何代码变更。

## 潜在风险
无。README 文件内容正确，未修改任何代码。
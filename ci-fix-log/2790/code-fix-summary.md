# 修复摘要

## 修复的问题
无代码修改。CI 失败属于基础设施问题：appstore 发布规范预检流水线 (`update.py`) 错误地对根级 README 文档文件执行了应用镜像发布路径校验，导致纯文档 PR 被误判为路径不合规。

## 修改的文件
无。PR 修改的 `README.md` 和 `README.en.md` 内容正确（新增 24.03-lts-sp3、25.09 等镜像 tag 文档链接），无需修改。

## 修复逻辑
CI 失败根因在 `eulerpublisher/update/container/app/update.py` 的 appstore 发布检查脚本中，该脚本假定所有 PR 变更都与应用镜像发布相关，缺少对根级 `README.md`、`README.en.md` 等纯文档文件的白名单豁免逻辑。PR 中变更的 README 文件本身没有问题，属于合法的文档更新。修复应指向 CI 基础设施而非本 PR 的变更文件：

- **方案一（推荐）**：在 CI trigger job 层面对纯文档 PR 进行过滤，跳过下游 appstore 发布检查流水线。
- **方案二**：在 `update.py` 中为根级 `README.md`、`README.en.md` 等文件增加路径跳过/豁免逻辑。

由于 `update.py` 不在 `pr.changed_files` 允许修改的范围内，且 README 文件本身无 bug，本次不进行代码修改。

## 潜在风险
无（未修改任何代码）。
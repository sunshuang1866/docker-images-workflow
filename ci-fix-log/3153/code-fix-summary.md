# 修复摘要

## 修复的问题
CI 基础设施问题（infra-error），无需修改 PR 代码。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告指出，失败类型为 **infra-error**，根因在于 CI 流水线中的 `eulerpublisher/update/container/app/update.py` 对所有 PR 变更文件强制执行 appstore 路径校验。本 PR（#3153）仅变更了 repo 根目录下的 `README.md` 和 `README.en.md` 两个纯文档文件，这些文件不属于应用镜像发布目录结构（`{category}/{image}/…`），被校验器误判为路径错误。PR 的文档变更内容本身（更新基础镜像可用 Tags 列表）没有任何质量问题。

修复应发生在 CI 流水线代码（`update.py`）中，使其在 PR 变更文件全部为 repo 根目录文档文件时跳过 appstore 路径校验。该文件不在本 PR 的 `pr.changed_files` 列表中，因此本次不进行任何代码修改。

## 潜在风险
无——未对源码仓库做任何修改，不影响任何功能。
# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 infra-error——CI 基础设施的 appstore 预检工具 `update.py` 将仓库根目录的 `README.md` 错误地纳入了镜像发布路径校验范围。

## 修改的文件
无。`README.md` 无需修改。

## 修复逻辑
根据 CI 失败分析报告，失败的根因是 `eulerpublisher/update/container/app/update.py` 中的 appstore 发布规范预检工具对所有 `git diff` 输出的变更文件一律执行路径格式校验，未区分"仓库级文档变更"与"镜像发布变更"。仓库根目录的 `README.md` 不在任何镜像目录（如 `Bigdata/`、`AI/` 等）之下，不满足 appstore 镜像发布路径结构规范，被误判为路径错误。

PR #3153 仅更新了 `README.md` 中基础镜像可用 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 等条目），改动完全合法，与 CI 失败无因果关系。该问题需要由 CI 平台维护者调整 `update.py` 的检查逻辑（如对仓库根目录的非镜像目录文件做豁免过滤），而非修改 PR 代码。

## 潜在风险
无。PR 代码无需修改，不存在引入新问题的风险。
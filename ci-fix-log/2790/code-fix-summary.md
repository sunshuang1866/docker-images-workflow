# 修复摘要

## 修复的问题
无代码修改。本次 CI 失败为基础设施错误（infra-error）：appstore 发布规范预检工具对根目录文档文件（`README.md`、`README.en.md`）进行了不应执行的路径校验，这些文件是本仓库的项目顶层文档，不应被纳入应用镜像路径规范的校验范围。

## 修改的文件
无。PR 修改的文件（`README.md`、`README.en.md`）内容合法正确，无需修改。

## 修复逻辑
CI 分析报告明确指出：PR #2790 仅更新了两个根目录文档文件的 Supported Tags 列表，改动本身合法正确。失败原因是 CI 流水线中的 `eulerpublisher/update/container/app/update.py:273` 对 PR 中所有变更文件无条件执行 appstore 镜像路径校验（期望路径为 `{category}/{image}/{version}/{os-version}/` 层级结构），根目录文档文件（`README.md`、`README.en.md`）天然不满足该规范，被误判为 `[Path Error]`。

此为 CI 校验逻辑过度覆盖问题，属于基础设施层面错误，不应通过修改 PR 文件来规避。真正需要修复的是 CI 流水线配置：
- 在 `update.py` 中将根目录项目文档文件（如 `README.md`、`README.en.md`、`.claude/README.md` 等）加入豁免名单
- 或在上游 trigger 流水线中增加判断：若 PR 变更仅为文档类文件则跳过 appstore 校验步骤

由于上述修复位置不在 `pr.changed_files` 允许修改的文件范围内，本次不进行代码修改。

## 潜在风险
无。本摘要未修改任何源码文件。
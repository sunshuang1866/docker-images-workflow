# 修复摘要

## 修复的问题
无需代码修改——CI 失败原因是外部 appstore 校验工具 `eulerpublisher/update/container/app/update.py` 对根目录 `README.md` 的路径校验存在误判，PR #3153 的 README.md 变更内容本身正确无误。

## 修改的文件
无。PR #3153 仅修改了 `README.md`（文档更新），其内容正确，无需改动。

## 修复逻辑
CI 分析报告明确指出：
- "PR 代码变更本身内容正确"
- "失败原因是 CI appstore 路径校验器对根目录 README.md 的路径判定与预期不符，属于 CI 校验层面的问题，而非 PR 变更内容有问题"

此问题需要在外部工具 `eulerpublisher/update/container/app/update.py`（位于 [EulerPublisher](https://gitee.com/openeuler/eulerpublisher) 仓库）中修复路径校验逻辑，例如：
- 将仓库根目录级文档文件（如 `/README.md`、`/README.en.md`）加入 appstore 校验的豁免/白名单列表；
- 或修正 `update.py` 中 `git diff` 输出前缀（`a/`、`b/`）的剥离逻辑。

由于该工具不在当前源码仓库内，且不在允许修改的文件列表中，本仓库无需也不应进行任何代码变更。

## 潜在风险
无。该修复不影响本仓库任何文件，PR 可被视为 CI 工具误报造成的阻塞，待 CI 工具修复后重新触发构建即可通过。
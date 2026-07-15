# 修复摘要

## 修复的问题
CI appstore 发布规范预检工具对根目录 `README.md` 产生路径校验误报（false positive），该失败与 PR 改动内容无关。实际根因是 CI 工具 `eulerpublisher/update/container/app/update.py` 未排除仓库根目录级别的项目级文档。

## 修改的文件
- 无代码修改。`pr.changed_files` 仅包含 `README.md`，而实际需要修复的是 `eulerpublisher/update/container/app/update.py`（路径校验逻辑），该文件不在允许修改的范围内。

## 修复逻辑
该失败是 CI 基础设施层面的工具误报：
1. PR #2790 仅修改了根目录 `README.md` 的文档内容（更新镜像 Tag 列表），变更内容正确合理
2. CI appstore 预检工具通过 git diff 检测到 `README.md` 变更后，将其纳入 appstore 镜像路径校验流程
3. 根目录 `README.md` 是项目级文档而非应用镜像文档，其路径格式不满足 appstore 镜像目录结构规范（如 `AI/<image>/README.md`），导致误报 FAILURE
4. 分析报告明确指出："该失败与 PR 改动内容本身无关，任何修改根级 README.md 的 PR 都会触发同样的误报"

正确的修复方向：在 CI 工具 `eulerpublisher/update/container/app/update.py` 的 diff 检测或路径校验阶段，将仓库根目录的项目级文档（`README.md`、`README.en.md` 等）从 appstore 镜像路径校验范围中排除。此修复需要 CI 工具维护者单独处理，不在当前 PR 的文件范围内。

## 潜在风险
无。README.md 的文档内容变更本身正确且不影响任何构建或发布流程。
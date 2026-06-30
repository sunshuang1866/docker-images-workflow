# 修复摘要

## 修复的问题
CI appstore 路径校验工具 (`update.py`) 误将仓库根目录的 README 文件纳入校验范围导致失败。属于 infra-error，无需修改 PR 代码。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告明确指出失败类型为 **infra-error**：PR #2790 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新可用镜像 Tags 列表），这些是纯文档更新，内容正确且无害。CI 失败根因是 `eulerpublisher/update/container/app/update.py` 在收集 PR diff 文件并进行 appstore 路径校验时，未排除仓库根目录下的项目级 README 文件，导致误报"Path Error"。

实际修复需要修改 CI 工具 `update.py`，为其增加对仓库根目录 README 文件的过滤排除逻辑，但该文件不在 PR 的 `changed_files` 列表中（`README.en.md`, `README.md`），不在此修复范围内。PR 本身的改动无需任何修改，可直接合并。

## 潜在风险
无。PR 文档改动不涉及任何 Dockerfile、镜像构建、测试代码或元数据文件，不影响任何镜像构建流程。
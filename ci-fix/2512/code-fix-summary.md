# 修复摘要

## 修复的问题
修复了 CI 失败分析报告中识别出的 3 个问题：提交了不应提交的 `__pycache__` 字节码文件、`submit_pr.py` 中存在残留的 `.agents/` 旧路径引用、Dockerfile 中 `LD_LIBRARY_PATH` 引用了未创建的 `/opt/3fs/lib` 目录。

## 修改的文件
- `.claude/__pycache__/run_workflow.cpython-313.pyc`: 从 Git 版本控制中移除（`git rm --cached`），该文件是 Python 构建产物，不应提交到仓库
- `.claude/scripts/submit_pr.py`: 将第 84、85 行注释中的 `.agents` 更新为 `.claude`，与 `.agents/` → `.claude/` 目录重命名保持一致
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在 `mkdir -p` 命令中补充 `/opt/3fs/lib` 目录创建，与 `ENV LD_LIBRARY_PATH=/opt/3fs/lib:...` 保持一致

## 修复逻辑
1. **问题 1（分析报告问题 1 — 高置信度）**: `.claude/__pycache__/run_workflow.cpython-313.pyc` 是 Python 3.13 的字节码缓存文件，属于构建产物，不应纳入版本控制。CI 流水线可能因检查到二进制文件或不符合 `.gitignore` 规则而失败。使用 `git rm --cached` 将其从索引中移除。
2. **问题 2（分析报告问题 2 — 高置信度）**: 原始 PR 将 `.agents/` 目录重命名为 `.claude/`，但 `submit_pr.py` 中的 2 行注释（第 84、85 行）仍写着 `.agents`，属于重命名后未更新的残留引用。虽然这些是注释行不会影响运行时行为，但可能导致代码审查或 lint 工具检测到不一致。
3. **问题 3（分析报告问题 3 — 中置信度）**: Dockerfile 第 33 行 `mkdir -p` 创建了 `/opt/3fs/bin` 和 `/opt/3fs/etc`，但没有创建 `/opt/3fs/lib`，而第 44 行 `ENV LD_LIBRARY_PATH` 却引用了 `/opt/3fs/lib`。补充该目录的创建可避免运行时库加载路径不存在的问题。

## 潜在风险
- `__pycache__` 文件从 Git 索引中移除后，本地文件系统仍保留该文件（使用了 `--cached` 参数）。后续提交时不会包含此文件，无负面影响。
- `submit_pr.py` 的修改仅涉及注释内容，不影响任何逻辑行为，无风险。
- Dockerfile 中补充 `/opt/3fs/lib` 目录创建是纯增量操作，不影响现有构建流程。但需要注意：如果后续构建步骤需要向 `/opt/3fs/lib/` 中复制库文件，该目录现已就绪。
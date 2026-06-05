# CI 失败模式知识库

本文件由 ci-fix-team 自动维护，记录历史 CI 失败的根因与修复模式，供 AI 分析时参考。


---

## openeuler/openeuler-docker-images PR #2512 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定（CI 日志缺失）` |
| 置信度 | 低 |

**根因**:


**修复方法**:
修复了 CI 失败分析报告中识别出的 3 个问题：提交了不应提交的 `__pycache__` 字节码文件、`submit_pr.py` 中存在残留的 `.agents/` 旧路径引用、Dockerfile 中 `LD_LIBRARY_PATH` 引用了未创建的 `/opt/3fs/lib` 目录。

**涉及文件**:
- `.claude/__pycache__/run_workflow.cpython-313.pyc`: 从 Git 版本控制中移除（`git rm --cached`），该文件是 Python 构建产物，不应提交到仓库
- `.claude/scripts/submit_pr.py`: 将第 84、85 行注释中的 `.agents` 更新为 `.claude`，与 `.agents/` → `.claude/` 目录重命名保持一致
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在 `mkdir -p` 命令中补充 `/opt/3fs/


---

## openeuler/openeuler-docker-images PR #2516 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定**（CI 日志不可用）` |
| 置信度 | 低** |

**根因**:
- 失败位置: 未知（缺少日志）
- 失败原因: 无法确定

**修复方法**:
`meta.yml` 文件末尾缺少换行符，可能导致 YAML 解析器/lint 检查报错。

**涉及文件**:
- `AI/vllm-cpu/meta.yml`: 在文件末尾补上换行符


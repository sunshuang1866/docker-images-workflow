# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: lint-error / build-error（基于 diff 推测，CI 日志不可用）
- 置信度: 低

## 根因分析

### 直接错误
CI 日志不可用，无法提供直接错误信息。以下分析完全基于 PR diff 推断潜在失败点。

### 根因定位

**⚠️ 重要声明**：`ci.logs` 字段标注为 `"(not available — analyze based on PR diff only)"`，因此以下所有分析均为基于 diff 的推测，**无法确认 CI 实际失败原因**。

基于 diff 分析，存在以下 **3 个高概率导致 CI 失败的候选根因**：

| 优先级 | 候选根因 | 影响文件 | 问题描述 |
|--------|----------|----------|----------|
| **P0** | 二进制缓存文件被提交 | `.claude/__pycache__/run_workflow.cpython-313.pyc` | `__pycache__/` 目录下的 `.pyc` 字节码文件被包含在 commit 中（`new_file: True, mode: 100644`）。这类文件不应进入版本控制，CI 通常有检查规则拒绝此类提交。 |
| **P1** | Dockerfile hadolint 违规 | `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:17` | `RUN bash -c "curl ... | sh -s -- ..."` 这种管道组合会触发 hadolint 规则 **DL4006**（`Set the SHELL option -o pipefail before RUN with a pipe in`），且 `curl | sh` 模式也存在安全隐患。 |
| **P2** | `category` 字段大小写不匹配 | `Storage/3fs/doc/image-info.yml:2` | `category: storage` 使用了全小写，但项目规范中场景分类名为 `Storage`。如果 CI 校验 `image-info.yml` 的 category 字段需匹配目录名 `Storage`（首字母大写），则可能失败。 |

### 与 PR 变更的关联

本 PR 的改动分两部分：

1. **目录重命名**（`.agents/` → `.claude/`）：涉及 10+ 个文件的移动/重命名，包括在 `.claude/__pycache__/` 下误提交了 `.pyc` 文件。这是本 PR **直接引入**的问题。

2. **新增 3FS 镜像**（`Storage/3fs/`）：新增 Dockerfile、README、image-info.yml、meta.yml、logo.png 等文件，`Storage/image-list.yml` 新增 `3fs: 3fs` 条目。其中 Dockerfile 的 `curl | sh` 管道写法是 **P0 候选根因**，属于本 PR 新引入。

三项候选根因**均与本次 PR 变更直接相关**，非历史遗留问题。

## 修复方向

### 方向 1 — 移除二进制 `.pyc` 文件（置信度: 高）
从版本控制中删除 `.claude/__pycache__/run_workflow.cpython-313.pyc` 文件，并在 `.gitignore` 中添加 `__pycache__/` 规则。如果已有 `.gitignore`，检查其是否覆盖 `.claude/` 子目录。

### 方向 2 — 修复 Dockerfile hadolint 违规（置信度: 中）
将 `RUN bash -c "curl ... | sh -s -- ..."` 改写为符合 hadolint 规范的写法：先 `curl` 下载脚本到文件，验证后再执行，或使用 `SHELL ["/bin/bash", "-o", "pipefail", "-c"]` 指令。

### 方向 3 — 统一 category 字段大小写（置信度: 低）
如果 CI 校验 `image-info.yml` 中的 `category` 字段需与目录名严格一致（`Storage` vs `storage`），则将 `category: storage` 改为 `category: Storage`。需确认 CI 的实际校验规则。

## 需要进一步确认的点

1. **CI 实际日志缺失**：当前分析完全基于 diff 推测。需要获取 Jenkins job `jenkins-from-comment` 的实际失败日志才能确认真正根因。
2. **CI 检查规则集**：需确认该仓库的 CI 流水线具体执行哪些检查（如 hadolint、yamllint、文件类型检查、目录结构校验等），以判断哪个候选根因实际触发了失败。
3. **`.gitignore` 现状**：确认仓库根目录的 `.gitignore` 是否已配置 `__pycache__/` 规则，以及该规则是否能覆盖 `.claude/__pycache__/` 路径。
4. **`category` 字段校验规则**：确认 CI 是否校验 `image-info.yml` 中的 `category` 值需与场景目录名完全一致（大小写敏感），并参考其他已有镜像（如 `kudu`、`daos`、`alluxio`）在该字段的写法。
5. **`submit_pr.py` 中残留 `.agents` 引用**：`submit_pr.py:82-83` 的注释仍写 `# Unstage .agents if it got staged`，如果后续代码逻辑也引用了 `.agents` 而非 `.claude`，则可能在后续 CI 步骤中引发运行时错误——但 diff 截断未展示完整上下文，需查阅完整文件确认。

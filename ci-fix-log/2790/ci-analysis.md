# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`update.py`) 对 PR 中变更的所有文件执行路径校验，该 PR 仅修改根级文档文件 `README.md` 和 `README.en.md`（不涉及任何 Dockerfile 或镜像文件），但 check 仍将其作为 appstore 条目进行路径校验，导致两份 README 文件均未通过预期的路径规范检查。

### 与 PR 变更的关联
PR 变更内容为纯文档更新：在 `README.md` 和 `README.en.md` 中增补了新的可用镜像 Tags（如 `25.09`、`24.03-lts-sp3`），不涉及任何 Dockerfile、image-list.yml 或其他构建/镜像文件。CI 失败由 appstore 发布规范预检工具对非镜像文档文件的过度校验导致，与 PR 变更内容无直接关联。该 PR 本身不应触发镜像发布规范检查。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具 (`eulerpublisher/update/container/app/update.py`) 的 diff 分析逻辑未区分"根级文档文件"和"镜像条目文件"，导致对纯文档 PR 也强制执行路径校验。需要在 update.py 的 diff 处理阶段增加过滤逻辑，将 `README.md`、`README.en.md` 等根级纯文档文件排除在 appstore 路径校验之外。

### 方向 2（置信度: 低）
检查 PR 分支 `sunshuang1866:fix/2790` 的仓库结构是否异常（如 README 文件是否被移到了非标准位置），导致 CI 克隆后识别出的路径与主分支不一致。但根据 diff 内容（仅修改 `README.md` 和 `README.en.md` 的文件内容），此可能性较低。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 diff 处理和路径校验逻辑的完整实现，确认是否存在将根级 `README.md`/`README.en.md` 错误纳入 appstore 路径校验的 bug。
2. 确认 PR 分支的仓库结构与主分支一致，README 文件确实位于仓库根目录 `/`。
3. 确认该 CI job（`x86-64` 架构的 appstore 预检）是否应对所有 PR 执行还是仅对包含镜像文件变更的 PR 执行；当前触发条件可能过于宽泛。

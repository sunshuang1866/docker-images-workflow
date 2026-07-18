# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（部分匹配）
- 新模式标题: 根级文件路径校验误杀
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范检查工具（`update.py`）对所有 PR 的变更文件执行路径校验。根级 `README.md` 不在任何应用镜像目录（如 `AI/`、`Bigdata/` 等）的路径模板范围内，工具无法将 `README.md` 映射到任何有效的 appstore 发布路径，导致路径校验失败。此检查对于不涉及任何应用镜像发布的纯文档 PR 不应触发，属于 CI 流水线阶段适用范围错误。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录下的两个文件：
- `README.md`：新增 25.09、24.03-lts-sp3 tag 条目，修正 latest tag 从 sp2→sp3 以及对应链接从 LTS-SP1→LTS-SP3
- `README.en.md`：同上改动

共计 4 行新增、1 行删除，不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等发布元数据文件。CI 的 appstore 发布规范检查将所有 PR 无差别纳入校验范围，导致纯文档修改被误判为不符合规范的发布变更。

## 修复方向

### 方向 1（置信度: 中）
PR 的变更内容（更新 README 中的可用 tag 列表）本身是正确的。问题在于 CI 流水线的 appstore 发布规范检查阶段未区分"应用镜像发布 PR"和"文档维护 PR"，对根级 `README.md` 执行了不适用于该场景的路径校验。修复应在 CI 工具侧：让 `update.py` 在校验文件前先过滤出属于应用镜像目录的变更，忽略根级非发布文件（如 README.md、README.en.md、.gitignore 等）。

### 方向 2（置信度: 低）
如果该仓库的 CI 策略要求**所有** PR（包括纯文档修改）都必须通过 appstore 发布规范检查，则报错信息揭示了 `update.py` 路径匹配逻辑的一个边界情况：工具可能使用 `README.md`（无前导 `/`）与预期路径模式匹配，而预期模式为 `/README.md`（有前导 `/`），前缀 `/` 差异导致匹配失败。需要确认 `update.py` 中的路径规范化逻辑是否对根级文件做了正确处理。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的路径校验逻辑具体如何工作——它是如何从 git diff 提取文件路径、如何与预期的 appstore 路径模板进行匹配的。
2. 该仓库的 CI 策略是否允许修改根级 `README.md` / `README.en.md`，或者是否要求文档修改通过单独的审批路径。如果该仓库原则上禁止非应用镜像目录的修改，则需要确认允许编辑根级文档的合规通道。
3. 日志中检测到的变更文件仅 `["README.md"]`，但 PR diff 同时包含 `README.en.md`。需确认 `update.py` 的文件变更检测范围（是否仅检查特定文件后缀，或者 `README.en.md` 在别的检查阶段被处理）。

## 修复验证要求
不适用——建议的修复方向均为 CI 流水线配置/工具逻辑调整，不涉及正则在外部源文件中的匹配修改。

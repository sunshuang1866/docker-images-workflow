# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（与模式11"YAML / 元数据文件错误"中的 CI appstore 发布规范预检子类有一定关联，但症状不同）
- 新模式标题: 文档变更误触预检
- 新模式症状关键词: README.md, Path Error, expected path, appstore, releasing specification, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-[...]/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: 无法定位到具体源文件行号（失败在 CI 脚本 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范预检工具（eulerpublisher）对 PR 中变更的 `README.md` 报告了 `[Path Error] The expected path should be /README.md`，但该文件在 PR diff 中确认位于仓库根路径 `/README.md`，与实际期望路径一致。这是一个 CI 预检工具的误报（false positive）——PR 仅包含文档内容修改（更新可用基础镜像 tag 列表），不涉及任何文件移动或路径变更。

### 与 PR 变更的关联
**与 PR 变更无实质关联。** PR #3153 的改动仅限于两个 README 文件的内容更新：
- `README.md`：将第一条 tag 从 `24.03-lts-sp2, 24.03, latest`（链接为 SP1 地址）更新为 `24.03-lts-sp4, 24.03, latest`（链接为 SP4 地址），并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 三条 tag 记录
- `README.en.md`：同上
这些改动不涉及任何文件创建、删除、移动或路径修改。CI 的 appstore 预检工具错误地将此文档变更判定为路径违规。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检工具（`eulerpublisher/update/container/app/update.py`）在检查纯文档类 PR（仅修改 README.md / README.en.md）时存在误判逻辑。需要排查 `update.py:222-273` 附近的路径校验逻辑，确认其对根级 `README.md` 的处理是否存在边界条件 bug。此问题应由 CI/基础设施团队修复，而非 PR 作者。

### 方向 2（置信度: 低）
CI 预检工具的 diff 解析可能遗漏了 `README.en.md`（日志中仅显示 `Difference: ["README.md"]`），导致后续校验上下文不完整。如果工具期望 PR 中两个 README 文件同时变更但只检测到一个，可能触发意外的路径校验错误。

## 需要进一步确认的点
1. CI 日志中仅显示检测到 `README.md` 的变更，而 PR diff 明确包含 `README.en.md` 的变更。需要确认 eulerpublisher 的 diff 检测逻辑是否遗漏了 `README.en.md`。
2. 需要查阅 `eulerpublisher/update/container/app/update.py:273` 周围的源码逻辑，理解 appstore 预检对 `README.md` 的具体校验规则，确认是何条件触发了 `Path Error`。
3. 确认该 CI 预检步骤是否为所有 PR 的必经环节，还是仅在特定条件下（如 PR 来自 fork、特定 label 等）触发。
4. 由于 CI 日志中的 PR 编号显示为 PR 3184，而上下文标记为 #3153，需要确认编号对应关系是否正确（可能是 trigger 系统与 PR 系统的编号不一致）。

# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (N/A — 匹配已有模式)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检对 `README.md` 执行路径校验，报告"期望路径应为 `/README.md`"并判定失败。但 `README.md` 实际上**已在仓库根目录 `/README.md`**，错误信息存在自相矛盾。其根本原因可能是：CI appstore 预检工具针对 PR diff 中仅包含根级 README 变更（无伴随的 app Dockerfile / meta.yml 提交）的纯文档更新场景，产生了误报。

### 与 PR 变更的关联
PR 仅修改了两个根级文档文件 `README.md` 和 `README.en.md`（更新支持标签列表、补充 25.09 / 24.03-lts-sp3 / 24.03-lts-sp2 等条目）。这些变更是纯文档更新，不包含任何 Dockerfile、meta.yml 或 image-list.yml 变更。CI 的 appstore 预检步骤检测到 `README.md` 出现在 diff 中后，触发了面向"新应用上架"的路径合规校验，而该校验的匹配规则在纯文档 PR 场景下产生误报（期望路径已满足却仍报 FAILURE）。

## 修复方向

### 方向 1（置信度: 中）
此失败属于 CI appstore 预检工具的误报，**PR 本身无需修改**。从历史模式（模式11）来看，同类 CI 预检失败（如 `.claude/agents/README.md` 路径校验）均通过调整文件路径或 CI 校验规则解决。本案例中 `README.md` 已位于正确路径，建议：
- 确认 CI 的 `update.py` 中 `_parse_diff` / `_check_path` 相关逻辑是否正确处理了根级文件路径（如 `README.md` vs `/README.md` 的前缀拼接）
- 若 CI 工具侧不可修改，可尝试在 PR 描述或 label 中标注 `docs-only` 跳过 appstore 预检
- 参考模式11 中根级文档路径问题的历史处理方式（如 PR #2512 `.claude/agents/README.md` → `.claude/README.md`），但本案例中文件已在正确位置，不存在需要移动的场景

### 方向 2（置信度: 低）
若 CI 预检的意图是"所有触发 CI 的 PR 必须包含至少一个 app 级别的合规变更"，而纯文档 PR 不应触发 appstore 预检流程，则可能是 CI trigger 层的问题——应将 appstore 预检的门槛限制为"PR diff 中涉及 `{category}/{app}/*/Dockerfile` 或 `meta.yml` 才执行"。

## 需要进一步确认的点
1. CI 工具 `update.py` 第 273 行前后 `_check_path` / `_validate_diff` 的完整逻辑：如何将 diff 中 `README.md` 映射到校验项，以及路径匹配规则是否存在前缀拼接 bug（导致根级 `README.md` 无法匹配 `/README.md`）。
2. PR 是否仅此一次触发 CI 失败：若多次重试仍复现，排除瞬态 infra 故障，确认是校验逻辑本身的问题。
3. 此 CI 预检是否对纯文档 PR 本不应触发：查看 trigger 层是否有 `paths-ignore` 或 `paths` 过滤条件可排除仅变更 `*.md` 文件的 PR。

## 修复验证要求
若修复方向涉及修改 CI 脚本中 README 路径匹配逻辑，code-fixer 必须：
1. 从 `eulerpublisher` 仓库获取 `update/container/app/update.py` 第 270-280 行的路径校验源码
2. 构造测试用例：验证 diff 中仅包含 `README.md`（根级文件）时能否正确匹配到 `/README.md` 并判定 PASS
3. 同时验证正常 app README（如 `AI/foo/README.md`）的路径校验不受影响

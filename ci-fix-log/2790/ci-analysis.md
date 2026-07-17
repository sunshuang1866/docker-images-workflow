# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

此外，CI 工具在差异检测阶段仅识别到 README.md 有变更（未包含 README.en.md）：
```
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py`:273（appstore 发布规范校验阶段）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 中变更的 `README.md` 执行路径规范校验时判定 FAILURE，错误描述为 `[Path Error] The expected path should be /README.md`。

### 与 PR 变更的关联

PR 仅修改了两个根级文件 `README.md` 和 `README.en.md`，内容变更为更新支持标签（Tags）列表：
- 将 `latest` 标签从 `24.03-lts-sp2` 改为 `24.03-lts-sp3`，对应 URL 从 SP1 改为 SP3
- 新增 `25.09`、`24.03-lts-sp3`（独立条目）、`24.03-lts-sp2`（独立条目）
- 注：`24.03-lts-sp3` 在变更后的文件中出现了两次（一次作为 latest 标签组合，一次作为独立条目），属于内容格式上的冗余

CI 失败是由文件变更触发的 appstore 规范预检导致的，但需要注意的是：

1. **文件确实存在于根路径**：Git diff 明确显示 `README.md` 位于仓库根目录（`a/README.md` → `b/README.md`），与 CI 提示的期望路径 `/README.md` 语义一致。
2. **错误含义不明确**：「The expected path should be /README.md」有三种可能的解读：
   - CI 工具在路径比较时存在格式差异（如缺少/多余前导 `/`、大小写敏感等），导致字符串匹配失败；
   - CI 工具在解析 PR 变更后发现 `README.md` 不在 appstore 规范的允许文件列表中（即根级 README.md 不属于任何镜像规格文件）；
   - CI 工具对 README.md 的内容格式（如内部链接路径指向的有效性）进行了额外的路径校验，变更后的内容触发了某个校验规则。
3. **仅 README.md 被检测**：虽然 PR 同时修改了 `README.md` 和 `README.en.md`，但 CI diff 检测仅报告 `README.md`，说明 CI 校验工具可能仅针对中文 README（或仅针对 `.md` 文件的特定子集）执行 appstore 规范检查。

**结论**：失败由 PR 的 README.md 变更触发，但日志提供的错误信息不足以精确定位为何一个已存在于根路径的 README.md 会触发 [Path Error]。这与模式11中 PR #2512 的多起 `.claude/README.md` 路径校验失败案例高度相似——均为 CI appstore 发布规范预检对 README 文件路径的校验逻辑触发了本不应触发的失败。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 规范校验工具（`eulerpublisher/update/container/app/update.py`）对 `README.md` 的路径校验逻辑存在缺陷——可能未将仓库根级 `README.md` 纳入白名单，或路径格式比较存在不一致。修复方向为检查该工具的路径校验规则，确认根级 README.md 是否应被跳过或应被纳入允许列表。

### 方向 2（置信度: 低）
PR 中 README.md 的内容变更引入了格式问题（如 `24.03-lts-sp3` 重复条目、或内部链接格式），CI 规范校验工具误将其归类为 [Path Error]。修复方向为检查 README.md 变更后的内容是否符合 appstore 规范的所有格式要求。

## 需要进一步确认的点

1. **eulerpublisher 源码确认**：需要查阅 `eulerpublisher/update/container/app/update.py:273` 附近的代码逻辑，理解 [Path Error] 的具体触发条件（即什么情况下会输出「The expected path should be /README.md」）。
2. **PR 分支的文件结构**：确认 CI 在 clone PR 分支（`sunshuang1866:fix/2790`）后，`README.md` 的实际路径是否确实为 `/README.md`（排除因分支设置导致文件位于非预期路径的可能性）。
3. **CI 允许路径列表**：确认 appstore 规范校验工具是否维护了一个「允许变更的文件路径」白名单，以及 `README.md`（根级）是否在该白名单内。
4. **README.en.md 是否应被检查**：PR 同样修改了 `README.en.md` 但未出现在 CI 差异列表中，需要确认这是预期行为还是 CI 工具的遗漏。

## 修复验证要求

由于修复方向存在不确定性（置信度为中），code-fixer 在实施修复前必须：
- 从 `eulerpublisher` 仓库获取 `update/container/app/update.py` 源码，确认第 273 行附近的路径校验逻辑，明确 [Path Error] 的触发条件和判定标准；
- 对照该逻辑验证根级 `README.md` 的路径（`/README.md` 或 `README.md`）是否与校验期
- 当前日志来自 x86-64 架构 job，且日志末尾明确 `Finished: FAILURE`，因此不适用"日志显示成功但 PR 处于失败状态"的前置退出条件。失败发生在 appstore 规范预检阶段（非 Docker 构建阶段），日志完整反映了失败原因。

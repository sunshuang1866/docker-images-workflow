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
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

```
2026-06-29 15:21:37,042-...update.py[line:356]-INFO: Difference: [ "README.en.md", "README.md" ]
2026-06-29 15:21:41,552-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: CI 预检阶段 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范路径校验）
- 失败原因: CI 的 appstore 发布规范检查对 PR 变更的根级 `README.en.md` 和 `README.md` 报告路径错误。`README.en.md` 的路径不符合 CI 期望的 `/README.md`；`README.md` 的路径本身符合期望值 `/README.md`，却同样被报告失败，存在 CI 工具逻辑歧义。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 中的"可用镜像 Tags"列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，更新 latest 指向）。无任何 Dockerfile、image-list.yml、meta.yml 等镜像构建相关文件变更。CI 的 appstore 发布规范预检被触发后，校验变更文件的路径是否符合规范，`README.en.md` 因不在期望的 `/README.md` 路径而失败。`README.md` 虽路径与期望一致但仍被标记失败，证据不足以解释该矛盾。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检不接受根级 `README.en.md` 作为合法的变更文件路径，期望所有 README 类变更统一落在 `/README.md`。同时 `README.md` 本身被误报路径错误，可能是 CI 工具将所有失败条目标记为同一类错误，或 PR 仅含文档变更时被整体拒绝。修复方向为：确认仅修改根级 `README.md` 是否能够通过 CI 检查，或确认 `eulerpublisher/update/container/app/update.py:273` 对文档类 PR 的路径校验逻辑是否存在缺陷。

### 方向 2（置信度: 低）
PR 中 README 内容存在重复条目（`24.03-lts-sp3` 同时出现在"latest"行和独立行中），虽然 CI 未报告内容错误，但需确认是否触发了 CI 的某种一致性校验。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的具体校验逻辑是什么——它检查的是文件路径、文件内容、还是 diff 中的路径格式。
2. `README.md` 路径与期望 `/README.md` 完全一致却被标记失败的原因——是 CI 工具 bug、是 `README.en.md` 失败导致的连带标记，还是 CI 对纯文档类 PR 统一拒绝进入 appstore 发布流程。
3. 将 `README.en.md` 的变更合并到 `README.md`（仅保留单一 README 文件变更）是否能让 CI 通过。
4. PR 中新增的几个 Tag URL（如 `openEuler-25.09/docker_img/`）在当前时间点是否真实可用（可能存在上游未发布、URL 404 的情况，但本次 CI 未报此错误）。

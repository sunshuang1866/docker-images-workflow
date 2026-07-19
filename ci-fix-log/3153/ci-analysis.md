# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (匹配已有模式)
- 新模式症状关键词: (匹配已有模式)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 间接错误（差异检测日志）
```
2026-07-16 20:34:19,171-.../update.py[line:356]-INFO: Difference: ["README.md"]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 PR 变更文件中包含根目录 `README.md`。该文件不属于任何应用镜像的最小目录单元路径（如 `AI/xxx/`、`Bigdata/xxx/`），路径校验规则判定其不符合 appstore 镜像发布规范，报告 `[Path Error]`。

### 与 PR 变更的关联
PR 仅修改了两个根目录文档文件：
- `README.md`（添加 24.03-lts-sp4、24.03-lts-sp3、25.09 等新 tag 条目，修正 `latest` 所对应的 tag 从 sp2 → sp4 及对应 URL）
- `README.en.md`（同上，英文版本）

这些变更为纯文档维护，不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等构建或元数据文件。CI 的 appstore 发布规范预检将所有变更文件纳入路径校验范围，`README.md` 因处于仓库根目录而非应用镜像子目录，触发了路径校验失败。

**结论：此失败由 PR 文档变更触发，但 PR 本身内容合法且必要。CI 预检工具对纯文档 PR 缺乏豁免机制，属于 CI 流程层面的过度校验。**

## 修复方向

### 方向 1（置信度: 高）
PR 为纯文档更新，不包含任何应用镜像的 Dockerfile 或元数据变更，不应由 appstore 发布规范预检拦截。code-fixer 无需对 PR 代码做任何修改。应与 CI 维护方确认是否需要调整 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑，增加对纯文档 PR（仅变更根目录 `README.md`、`README.en.md` 等非应用镜像文件）的豁免规则。同类历史案例参见 模式11 中 PR #2512（`.claude/agents/README.md` CI appstore 路径校验失败，同样因文件路径不符合应用镜像目录结构规范而触发）。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑是否已有对仓库根目录级文件（非应用镜像路径）的豁免规则；若不存在，应作为 CI 工具改进追踪项，不应要求 PR 提交者修改代码来绕过此校验。
- 确认 CI 流程是否应按 PR `diff` 中的变更文件路径判断是否应跳过 appstore 发布规范检查（如 PR 仅涉及仓库根目录文档文件时直接跳过）。

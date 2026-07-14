# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 变更文件进行路径校验时，将仓库根目录的 `README.md` 路径判定为不符合预期格式（期望 `/README.md` 而检测到 `README.md`），实际两者等价，该校验对纯文档 PR 属于误报。

### 与 PR 变更的关联
PR 仅修改了两个文档文件（`README.md` 和 `README.en.md`），更新了基础镜像的可用 Tags 列表，未新增任何应用镜像 Dockerfile 或元数据文件。CI 的 appstore 发布规范预检被触发运行，对根级 README.md 执行了本不应适用于纯文档变更的路径校验，结果是 CI 工具层面的误报，与 PR 的实际代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
PR 仅包含 README 文档更新，不涉及任何应用镜像发布。该 CI 检查（appstore 发布规范预检）不应被文档类 PR 触发，或应对根级 README.md 路径做归一化处理。建议检查 CI trigger 逻辑是否可按 PR 变更文件类型跳过 appstore 规范检查，或修改 `update.py` 中路径比较逻辑将 `README.md` 与 `/README.md` 视为等价。

### 方向 2（置信度: 低）
若 CI 不便于按文件类型跳过检查，可在 `update.py` 路径校验逻辑中增加对仓库根目录文件（如 README.md、README.en.md）的豁免，使其不被视为 appstore 镜像发布条目进行校验。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中 `line:273` 附近的路径校验逻辑：确认为何 `README.md`（相对路径）与 `/README.md`（绝对路径）被判定为不匹配。
2. CI trigger 配置：确认 appstore 预检 job 的触发条件是否应排除纯文档变更的 PR。
3. 同类历史案例（模式11 中的 PR #2512 `.claude/agents/README.md` 路径校验失败）的修复方式，是否可作为参考。

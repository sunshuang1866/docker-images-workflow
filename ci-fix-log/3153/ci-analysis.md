# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径前缀缺失
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范校验工具检测到 PR 修改了根目录 `README.md`，但路径格式 `README.md`（无前导 `/`）与校验工具期望的规范路径 `/README.md`（有前导 `/`）不匹配，导致路径校验失败。PR 仅修改了 README.md 和 README.en.md 两个根级文档文件（更新基础镜像可用 tags 列表），属于纯文档变更。

### 与 PR 变更的关联
PR 的改动直接触发了此失败。PR 修改了仓库根目录的 `README.md` 和 `README.en.md`——将最新 tags 从 `24.03-lts-sp2` 更新为 `24.03-lts-sp4`，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目。CI 流水线对所有 PR 执行 appstore 发布规范预检，该预检检测到 `README.md` 的变更并将其路径与预期规范比对时失败。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `update.py` 在路径比较时存在前导 `/` 的不一致问题——检测到的路径为 `README.md`，而预期路径格式为 `/README.md`。需确认 `update.py:222-273` 中路径规范化逻辑是否存在 bug，或 PR 分支中 `README.md` 的路径在 clone 后未被正确解析为绝对路径。

### 方向 2（置信度: 低）
该 PR 仅修改根级 README 文档，不属于任何应用镜像的 appstore 发布范畴。CI appstore 预检可能不应对此类纯文档 PR 执行路径校验。需确认 CI 流水线配置是否缺少对文档类变更的跳过逻辑（如仅修改根级 `*.md` 文件时跳过 appstore 校验）。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 222-273 行的路径比较逻辑——路径是如何从 git diff 提取的，与预期路径 `/README.md` 的比对格式是否一致
2. 该 PR 的 CI 触发方式（日志显示 `PR 3184 [sunshuang1866:fix/3153 -> master]`，与 PR 编号 #3153 不一致），需确认实际 CI 运行的 PR 上下文是否正确
3. 该 appstore 路径校验是否应该对仅修改根级文档的 PR 放行（参考模式11 中 `.claude/README.md` 同类问题）
4. 上游 repo `sunshuang1866/****-docker-images` 中 clone 后的 README.md 文件路径是否与源仓库一致

## 修复验证要求
若修复方向涉及 `eulerpublisher/update/container/app/update.py` 中路径规范化逻辑的修改，code-fixer 必须：
- 从 eulerpublisher 仓库对应版本获取 `update.py` 源码，确认路径提取和比对逻辑（第 222-273 行）
- 在本地模拟 `git diff` 输出，验证修复后 `README.md` 与 `/README.md` 的比对能正确通过
- 确认修复不会影响其他子目录 README 文件的正常校验（如 `AI/xxx/doc/README.md` 等）

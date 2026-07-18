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
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

CI 检测到变更文件为 `README.md`（日志中 `Difference: ["README.md"]`），随后执行 appstore 发布规范预检。检查结果表显示 `README.md` 路径校验失败，描述为 `[Path Error] The expected path should be /README.md`，导致构建标记为 `FAILURE`。

### 根因定位
- 失败位置: eulerpublisher CI 工具 `update.py:273`（appstore 规范预检阶段）
- 失败原因: CI 的 appstore 发布规范校验器检测到 PR 修改了仓库根目录的 `README.md`，对其进行路径合法性检查时判定失败。该检查要求所有变更文件满足 appstore 镜像条目路径规范（如 `{category}/{image-name}/{version}/{os-version}/Dockerfile`），而根目录 `README.md` 不属于任何有效的 appstore 镜像条目路径，因此被标记为 `FAILURE`。

### 与 PR 变更的关联
PR #2790 仅修改了两个文档文件：
- `README.md` — 更新基础镜像可用 Tags 列表（将 `24.03-lts-sp2` 升为 `24.03-lts-sp3`，新增 `25.09` / `24.03-lts-sp3` / `24.03-lts-sp2` 条目）
- `README.en.md` — 同上（英文版）

PR 的文档内容变更本身**没有错误**，但 CI 流水线会对所有变更文件执行 appstore 规范校验，根目录 `README.md` 触发了该校验并因路径不符合 appstore 镜像条目规范而失败。这是一个 CI 校验规则与文档类 PR 的兼容性问题。

## 修复方向

### 方向 1（置信度: 中）
该 PR 为纯文档更新，不涉及任何 Dockerfile 或镜像构建文件。CI 的 appstore 规范校验器错误地将根目录 `README.md` 纳入了 appstore 镜像条目路径检查。修复思路是**联系 CI 维护方，将仓库根目录 `README.md` 和 `README.en.md` 加入 appstore 规范校验的白名单/排除列表**，使其不再被当作镜像条目文件进行路径校验。

### 方向 2（置信度: 低）
若该仓库的 appstore 规范要求所有 PR（包括文档类 PR）都必须带有有效的 appstore 镜像条目，则此 PR 可能需要**拆分**——将 README 文档更新与实际的镜像条目提交分离到不同的 PR 中。

## 需要进一步确认的点
1. **CI 校验工具 `update.py` 的确切路径校验逻辑**：需要查看 `eulerpublisher/update/container/app/update.py` 中第 222-273 行附近的 appstore 规范校验逻辑，确认根目录 README.md 是否应被排除在 appstore 路径校验之外。
2. **同类 PR 的历史行为**：确认该仓库中此前是否有过单独修改根目录 `README.md` 的 PR 通过了 CI 检查，以判断这是否为 CI 工具近期的回归问题。
3. **`README.en.md` 未被检查的原因**：日志中 `Difference` 列表仅包含 `README.md` 而不同时包含 `README.en.md`，需确认 CI 工具的文件过滤逻辑是否按扩展名或路径选择性检查变更文件。

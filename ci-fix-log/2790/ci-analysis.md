# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (无需填写)
- 新模式症状关键词: (无需填写)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验逻辑）
- 失败原因: CI 工具 `eulerpublisher` 的 appstore 发布规范校验模块在比对 `git diff` 输出的文件路径 `README.md`（不含前导 `/`）与预期路径 `/README.md`（含前导 `/`）时，由于路径格式不一致（相对路径 vs 绝对路径）导致字符串比较失败，从而错误地判定路径不符合规范。`README.md` 实际位于仓库根目录，路径本身没有问题。

### 与 PR 变更的关联
PR #2790 仅修改了两个 README 文件（`README.md` 和 `README.en.md`），属于纯文档更新（更新基础镜像 Tags 列表）。CI 的 diff 检测工具正确识别出 `README.md` 发生变更，随后触发了 appstore 发布规范校验。由于校验工具内部路径比较逻辑存在缺陷（未能标准化 `README.md` 和 `/README.md` 为同一路径），导致误报失败。此失败与 PR 的**具体内容变更无关**，属于 CI 工具自身的 bug。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施侧修复：修改 `eulerpublisher/update/container/app/update.py` 中 appstore 路径校验逻辑，在比较文件路径前进行标准化处理（例如对 `git diff` 输出的相对路径自动添加前导 `/`，或对预期路径 `strip` 掉前导 `/`），确保路径格式一致后再比较。

### 方向 2（置信度: 低）
若 `update.py` 中校验逻辑本身正确、而是校验规则的配置表中预期路径书写有误（如多写了前导 `/`），则修正配置表即可。

## 需要进一步确认的点
1. 查阅 `eulerpublisher` 工具源码中 `update.py` 第 273 行附近的路径校验逻辑，确认路径比较的确切实现方式。
2. 确认 PR #2512（同类 appstore 路径校验失败案例，涉及 `.claude/README.md`）的最终修复方式，以判断这类问题在历史中如何处理——是修正文件路径还是修正 CI 工具。
3. 确认 `README.md` 在仓库根目录之外是否还有其他位置存在同名文件干扰 diff 检测。

## 修复验证要求
无需验证——本失败为 CI 基础设施问题（infra-error），与 Dockerfile 构建或代码变更无关，不涉及正则 patch 外部源文件。

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检逻辑）
- 失败原因: CI 的 appstore 发布规范预检工具在扫描到 PR 修改了 `README.md` 后，对其路径进行了校验，但路径比对时发现 diff 输出的相对路径 `README.md`（无前导 `/`）与工具期望的绝对路径格式 `/README.md`（有前导 `/`）不一致，判定为 Path Error。

### 与 PR 变更的关联

PR #3153 仅修改了两个根目录下的 README 文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 tags 列表（如新增 `24.03-lts-sp4`、`25.09` 等条目）。PR 本身为纯文档变更，不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml。

失败由 CI 工具 `eulerpublisher` 的 appstore 发布规范预检步骤触发：该工具检测到 `README.md` 被修改，将其纳入 appstore 规范校验范围，路径格式化/比对环节产生误判。**PR 的文档内容变更本身不会触发此错误**，问题出在 CI 工具对根目录文件的路径处理逻辑上——路径的表述方式差异（相对路径 vs 绝对路径）被错误地识别为规范不符。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 在 appstore 路径规范校验时，对 diff 检测到的文件路径未做归一化处理。diff 输出的路径格式为 `README.md`（不含前导 `/`），而内部路径校验规则期望的格式为 `/README.md`（含前导 `/`）。应在路径比对前将两者统一为同一格式（均添加或均去除前导 `/`），避免对根目录文件的误判。此修复应作用于 CI 工具代码本身，而非 PR 的 Dockerfile 或 README。

### 方向 2（置信度: 低）
若路径比对逻辑无问题，则可能是 appstore 发布规范要求仓库根目录下 README.md 需要额外的元数据声明或路径映射条目，PR 修改触发了缺少此类声明的校验。但鉴于 PR 仅修改 README 内容且为纯文档变更，此可能性较低。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行及其上下的路径校验逻辑，确认路径格式化方式（是否统一使用 `os.path.normpath` 或类似归一化方法）。
2. 同类 CI 检查在其他仅修改根目录 README 的文档类 PR 上是否也失败，以确认是否为已知的 CI 工具 bug。
3. appstore 发布规范是否针对根目录 README.md 有特殊的路径声明要求（如需要在某 yml 中显式声明 `/README.md`），若有则需要了解该声明的格式和位置。

## 修复验证要求
code-fixer 在提交修复前，需确认 `eulerpublisher` 工具中 appstore 路径校验代码的实际比对逻辑：获取 `update.py:273` 附近代码上下文，确认路径字符串来源（diff 输出还是内部配置），验证归一化处理后对根目录文件（`README.md`、`README.en.md`）和非根目录文件（如 `Bigdata/xxx/README.md`）均能正确通过校验。

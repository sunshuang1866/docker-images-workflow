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
2026-07-16 20:34:43,051-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检工具）
- 失败原因: CI 预检工具（eulerpublisher）在扫描 PR 变更文件时，对根目录 `README.md` 执行 appstore 发布规范路径校验。工具期望路径格式为 `/README.md`（带前导 `/` 的绝对仓库路径），但 `git diff --name-only` 返回的路径为 `README.md`（不带前导 `/` 的相对路径），导致路径格式校验失败。

### 与 PR 变更的关联
**直接关联**。PR #3153 对 `README.md` 和 `README.en.md` 进行了修改（更新可用基础镜像 Tag 列表：新增 24.03-lts-sp4/sp3/sp2、25.09 条目，将 latest 标签从 sp2 改为 sp4）。CI 的差异检测确认变更文件为 `README.md`（日志：`Difference: ["README.md"]`），随后触发 appstore 发布规范检查，因路径格式问题报错。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 eulerpublisher 的 `update.py` 中路径比较逻辑未做归一化处理——`git diff` 返回的相对路径 `README.md` 与校验规则中期望的绝对路径 `/README.md` 不匹配。修复方向为：在 `update.py` 中为 `git diff` 输出的路径统一添加前导 `/`，使其与校验规则中的路径格式一致。具体修改位置应为路径提取/比较环节（在 line 273 报错之前），确保进入"appstore 发布规范检查"的路径均以 `/` 开头。

### 方向 2（置信度: 低）
若 `README.md` 需要满足 appstore 发布的特定内容规范（如必须包含特定章节、元信息或格式），则当前 README 的变更内容可能不符合该规范。但日志仅提示 `[Path Error]`，无内容格式相关报错，此方向可能性较低。

## 需要进一步确认的点
1. **eulerpublisher 源码**：需查看 `update.py` line 273 附近的路径校验逻辑，确认路径归一化代码的具体位置。
2. **appstore 发布规范文档**：确认根目录 README.md 是否有内容格式要求（如特定章节、元数据等），以排除方向 2 的可能性。
3. **验证路径格式**：手动运行 `git diff --name-only` 对比 `update.py` 中的路径比较逻辑，确认是否确实为前导 `/` 缺失导致的问题。

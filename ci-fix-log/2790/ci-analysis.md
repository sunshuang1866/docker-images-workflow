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
2026-07-14 15:28:07,685-[...]/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验阶段）
- 失败原因: CI 的 appstore 发布规范检查工具检测到变更文件 `README.md` 的路径格式不符合预期——工具要求路径以 `/` 开头（即 `/README.md`），但从 git diff 中提取的路径为 `README.md`（无前导 `/`），路径比对不匹配导致检查失败。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个仓库根级文档文件，无任何容器镜像相关的 Dockerfile、meta.yml 等文件变更。CI 的 appstore 发布规范检查在 PR 仅包含文档变更时仍然运行，对检测到的 `README.md` 执行路径格式校验，因路径缺少前导 `/` 而失败。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 在提取 git diff 文件路径后未进行路径归一化（添加前导 `/`），导致与预期路径 `/README.md` 比对失败。修复方式：在 `eulerpublisher/update/container/app/update.py` 中确保路径比对前将相对路径归一化为绝对路径形式（添加 `/` 前缀），或在路径比较逻辑中对两种格式做兼容处理。

### 方向 2（置信度: 低）
PR 仅修改了 README 文档，不涉及任何镜像发布内容，CI 的 appstore 检查本身不应被触发。修复方式：在 CI 编排流程中，当变更文件全部为仓库根级文档（README.md、README.en.md 等）且不含任何镜像子目录文件时，跳过 appstore 规范检查。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 的具体路径比较逻辑——需要查看该行源代码以确认路径格式校验的实现方式。
2. 该 PR 既然只修改了 `README.md` 和 `README.en.md` 两个文件，为何 CI 差异检测结果中只出现了 `README.md` 而遗漏了 `README.en.md`，需要确认 diff 提取逻辑是否仅取第一个变更文件。
3. 历史同类 PR（纯文档修改）是否也触发了此 appstore 路径校验——若历史上有纯文档 PR 通过 CI，则说明 CI 行为近期发生了变更。

## 修复验证要求
- 若修改 `eulerpublisher` 中的路径比较逻辑（方向 1），需在本地模拟 PR 变更场景，验证归一化后的路径能通过 appstore 校验。
- 若修改 CI 编排逻辑跳过纯文档 PR（方向 2），需确认历史纯文档 PR 的实际 CI 行为作为对照。

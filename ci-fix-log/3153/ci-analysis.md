# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 eulerpublisher 工具检测到 `README.md` 变更后，对其执行 appstore 发布规范路径校验。`README.md` 位于仓库根目录（即 `/README.md`），但路径比较逻辑产生误判（可能是 diff 输出的相对路径 `README.md` 与校验模板中的绝对路径 `/README.md` 存在前导斜杠不匹配），导致校验失败。

### 与 PR 变更的关联
PR 变更内容为纯文档更新——仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，更新了 openEuler 基础镜像的可用 tags 表格。这些变更与 Docker 镜像构建或 appstore 上架完全无关。CI 的 appstore 发布规范预检对根目录文档文件执行路径校验属于误报，不应将此类文件纳入 appstore 规范检查范围。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线中 eulerpublisher 的 `update.py` 应排除对仓库根目录下纯文档文件（如 `README.md`、`README.en.md`）的 appstore 路径校验。这些文件不受 appstore 上架规范约束，不应触发路径格式检查。可在 `update.py` 中增加文件过滤逻辑——在路径校验前判断变更文件是否位于仓库根目录且为已知文档文件，若是则跳过校验。

### 方向 2（置信度: 低）
路径比较逻辑本身可能存在前导 `/` 不一致的 bug。`git diff` 输出的文件路径通常不带前导 `/`（如 `README.md`），而校验模板可能使用 `/` 前缀的绝对路径（如 `/README.md`）。若这是根因，应在路径比对前统一做路径规范化（如统一添加或移除前导 `/`）。

## 需要进一步确认的点
- 需要查看 `eulerpublisher/update/container/app/update.py` 的实现逻辑，确认第 273 行错误输出和第 356 行 diff 检测之间的具体路径校验流程
- 需要确认 CI 设计中，仓库根目录的 `README.md` / `README.en.md` 是否被设计排除在 appstore 发布规范检查之外，还是当前实现遗漏了此过滤逻辑
- 需要确认为什么 `README.en.md` 同样被修改但未出现在 `Difference` 输出中（日志第 356 行仅列出 `README.md`），这可能有助于理解 diff 检测的范围设定

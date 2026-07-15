# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 预检工具）
- 失败原因: CI appstore 发布规范预检工具检测到根目录 `README.md` 被修改，但在路径校验时未能正确匹配该文件。工具报告 "The expected path should be /README.md"（期望路径应为 /README.md），说明根级 `README.md` 的相对路径表示（`README.md`，无前导 `/`）与工具内部期望的路径格式（`/README.md`）不匹配，导致校验失败。

### 与 PR 变更的关联
**PR 变更直接触发了该失败**。本 PR 为纯文档更新，仅修改了根目录下 `README.md` 和 `README.en.md` 中"可用镜像 Tags"章节的内容（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 条目，调整最新标记）。CI 差异检测识别出 `README.md` 变动后，将其送入 appstore 发布规范预检流程，而该预检工具对根目录文档文件的路径格式存在校验缺陷，导致本应通过的无害文档更新被视为不合规。

## 修复方向

### 方向 1（置信度: 高）
CI 预检工具 `eulerpublisher/update/container/app/update.py` 在扫描变更文件时，将根目录 `README.md` 纳入了 appstore 路径校验逻辑。该工具应增加对根目录级文件的白名单过滤（如 `.claude/README.md`、`README.md`、`README.en.md` 等非应用镜像文件），使其仅对 `Category/ImageName/Version/os-version/` 路径结构下的文件执行路径合规校验。

### 方向 2（置信度: 中）
修复 `update.py` 中路径比较逻辑，在比较前对文件路径统一进行规范化处理（补全前导 `/`），消除 `README.md` 与 `/README.md` 的差异。

## 需要进一步确认的点
- 需查阅 `eulerpublisher/update/container/app/update.py` 第 222-273 行之间（Difference 计算后到 ERROR 抛出前）的路径校验逻辑，确认具体的路径比较实现。
- 需确认 CI 预检工具是否应仅针对"新增"的文件执行路径校验，而对已存在于仓库中的根级文件（如 `README.md`）的修改予以跳过。

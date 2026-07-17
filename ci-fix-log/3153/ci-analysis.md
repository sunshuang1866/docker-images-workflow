# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI工具误检根级文档
- 新模式症状关键词: Path Error, The expected path should be, README.md, eulerpublisher, appstore, specification errors

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

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: `eulerpublisher` CI 工具对根级文档文件 `README.md` 错误地执行了 appstore 路径校验。该工具预期 appstore 相关变更应遵循 `{scenario}/{image}/{version}/{os-version}/Dockerfile` 等子目录结构，当 README.md 位于仓库根路径 `/README.md` 时，虽路径本身正确，但不满足 appstore 镜像目录的结构约束规则，导致工具将其标记为 `[Path Error]`。

### 与 PR 变更的关联
PR #3153 是一个**纯文档变更**，仅修改了 `README.md` 和 `README.en.md` 两个根级文件中的可用镜像 tag 列表（更新 24.03-lts-sp4 条目、新增 24.03-lts-sp3 / 25.09 / 24.03-lts-sp2 条目）。变更不涉及任何 Dockerfile、meta.yml、image-info.yml 或应用镜像目录。CI 失败是 `eulerpublisher` 工具在扫描变更文件时，将不属 appstore 范畴的根级 README.md 误纳入了 appstore 路径规范检查所致，属于 CI 工具缺陷，与 PR 实际改动内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher` 的 appstore 发布规范检查逻辑需要增加白名单或排除规则：当检测到变更文件位于仓库根级（如 `/README.md`、`/README.en.md`）且不属于任何 appstore 镜像子目录时，应跳过路径格式校验，直接通过。此修复需在 `eulerpublisher/update/container/app/update.py` 或其调用的校验模块中实现。

### 方向 2（置信度: 低）
若短期内无法修改 CI 工具代码，可通过在 PR 中补充或修正某些元数据文件（如在相应 `image-list.yml` 中添加根级文档的白名单条目）来绕过校验。但此方向缺乏日志证据支持，不推荐作为首选方案。

## 需要进一步确认的点
1. `eulerpublisher` 工具中 `update.py:273` 附近 appstore 路径校验的具体逻辑——是否对所有变更文件无差别执行校验，还是仅对匹配特定模式的文件执行。
2. 在当前仓库中，根级 `README.md` 的历史变更是否也曾触发过同样的 CI 失败（以确认这是回归还是已知问题）。
3. `update.py:356` 输出的 `Difference: ["README.md"]` 仅包含 `README.md` 而未列出 `README.en.md`——确认 diff 扫描逻辑的预期行为，以及 `README.en.md` 是否被遗漏或被独立校验。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——本问题不涉及对外部源文件的正则 patch。

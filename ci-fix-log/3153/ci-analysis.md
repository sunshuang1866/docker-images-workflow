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
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 中修改的根级 `README.md` 执行路径校验时失败。工具以无前导 `/` 的格式（`README.md`，来自 git diff）获取变更文件路径，但期望的路径格式带前导 `/`（`/README.md`），严格字符串比对不通过导致 FAILURE。该文件为仓库根级文档，不属于任何 appstore 镜像条目，不应触发 appstore 路径校验。

### 与 PR 变更的关联
PR 仅修改了两份根级 README 文档（`README.md` 和 `README.en.md`）中基础镜像 tag 列表的文本内容，属于纯文档更新。PR 变更本身无任何语法或格式错误。失败由 CI 工具在扫描变更文件时将所有文件纳入 appstore 路径校验逻辑导致——根级 README 不是 appstore 镜像条目，校验本应跳过或通过，但工具路径比对逻辑存在缺陷（前导 `/` 不匹配），实际上不属于 PR 代码变更引起的问题。

## 修复方向

### 方向 1（置信度: 中）
CI 工具的 appstore 路径校验逻辑存在缺陷：`update.py` 中比较变更文件路径与期望路径时使用严格字符串匹配，未对路径格式做规范化处理（补充或去除前导 `/`）。应在 `update.py` 的路径校验函数中增加 `os.path.normpath()` 或等效的路径标准化步骤，使 `README.md` 与 `/README.md` 能够正确匹配。此为 CI 工具修复，与 PR 代码变更无关。

### 方向 2（置信度: 低）
CI 工具不应将根级文档文件（如 `README.md`、`README.en.md`）纳入 appstore 发布规范校验范围。可在 `update.py` 的变更文件扫描阶段增加过滤逻辑，排除仓库根目录下不属于任何 appstore 镜像目录的文件，避免无意义的校验失败。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py:273` 附近路径校验逻辑的具体实现，验证 `README.md`（无前导 `/`）与 `/README.md`（有前导 `/`）的比对方式。
2. 确认 CI 工具是否设计为对所有变更文件（包括根级文档）都执行 appstore 校验，还是仅应校验 `image-list.yml` 中注册的镜像目录下的文件。
3. 日志中 CI 由 `PR 3184 [sunshuang1866:fix/3153 → master]` 触发，但分析指定为 PR #3153，建议确认两者关系以及实际失败对应的 PR 编号。

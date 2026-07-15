# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infa-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误

```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）检测到 `README.md` 发生变更后，对其执行了路径格式校验，但仓库根目录的 `README.md` 不属于应用镜像发布文件，不应当受 appstore 路径规范约束。CI 工具在对此文件进行路径校验时，因路径格式（/ 是否有 `/` 前缀等）不匹配预期而误报 `FAILURE`。

### 与 PR 变更的关联

PR #2790 的代码变更仅修改了两个文档文件：
- `README.md` — 更新基础镜像标签列表（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 独立条目，修正 latest 指向从 SP1/SP2 变为 SP3）
- `README.en.md` — 英文版同步更新

**PR 变更本身不会引起任何构建、测试或真正的发布失败。** CI 失败原因为 `eulerpublisher` 工具将仓库根目录 `README.md` 错误地纳入了 appstore 发布规范的路径校验范围，产生了与 PR 代码变更无关的误报。这与模式11 中 `.claude/README.md` 被 CI appstore 预检误报路径不符规范的问题属于同一类型。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `update.py` 的路径校验逻辑需要排除仓库根目录下的“非镜像发布”文件（如根目录 `README.md`、`README.en.md`），仅对实际的应用镜像目录下的文件执行 appstore 路径规范检查。需修改 `eulerpublisher/update/container/app/update.py` 中的变更文件过滤逻辑，在文件列表进入路径校验前过滤掉位于仓库根层的文档类文件。

### 方向 2（置信度: 中）
如果 CI 工具本身不支持排除特定文件，可在 PR 触发 CI 的编排层（jenkins pipeline 上游）增加判断：若 PR 变更列表仅包含根目录级文档文件（不含任何镜像子目录下的文件），则跳过 appstore 规范预检步骤。

## 需要进一步确认的点
1. `update.py:273` 中路径校验的具体逻辑——是精确字符串比较还是模式匹配？`README.md` 与 `/README.md` 的差异是缺少前导 `/` 导致，还是工具根本没有为根级 README 设计豁免规则？
2. 是否是仓库根目录 `README.md` 首次被 CI appstore 预检误报？（排查是否近期 CI 工具更新后引入了此行为变化）
3. 确认同一 PR 中 `README.en.md` 也被修改但未出现在 `Difference` 列表中的原因——是被 `update.py` 有意过滤还是巧合避开？

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本失败为 CI 工具对仓库自身文件的校验逻辑问题，不涉及第三方/上游源文件的正则匹配修改。）

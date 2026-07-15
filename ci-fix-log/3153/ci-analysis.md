# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, /README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验）
- 失败原因: CI 的 appstore 校验工具检测到 PR 变更了 `README.md`，对该文件执行路径校验。git diff 产出的路径为 `README.md`（无前导 `/`），而校验工具以 `/README.md`（带前导 `/`）作为期望路径进行字符串比较，二者不匹配导致误报 `FAILURE`。PR 仅修改了根目录 README 中的基础镜像 tags 列表，文件路径本身完全正确。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更是纯文档更新——仅修改 `README.md` 和 `README.en.md` 中基础镜像可用 tags 列表（添加 24.03-lts-sp4、24.03-lts-sp3、25.09 等条目）。这些变更是有效且正确的。CI appstore 校验工具对根级文档文件执行了本不应触发的路径格式检查，导致误报。CI 日志中 `update.py` 的 `Difference` 字段仅列出 `README.md`（未包含 `README.en.md`），进一步表明校验工具的变更文件识别与路径格式化之间存在不一致。

## 修复方向

### 方向 1（置信度: 低）
CI appstore 校验工具 `eulerpublisher/update/container/app/update.py` 需要对 git diff 产出的文件路径与校验规则中的期望路径做统一的路径格式化处理（均在首部添加 `/` 或均去除），以消除 `README.md` vs `/README.md` 的不一致。这是 CI 工具侧的问题，PR 代码本身无需修改。

### 方向 2（置信度: 低）
CI 流水线应在 appstore 校验环节排除根级纯文档文件（`README.md`、`README.en.md`、`LICENSE` 等），使文档类 PR 不触发 appstore 发布规范检查。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py:273` 上方路径比较逻辑的具体实现（`expected path` 的来源与 `actual path` 的格式化方式），以精确定位前导 `/` 不一致的代码位置。
- 确认该 CI 校验环节是否有白名单/排除列表机制，以及根级 `README.md` 是否应被收录。
- 确认 `Difference` 中仅出现 `README.md` 而未出现 `README.en.md` 的原因——是否仅校验特定文件模式。


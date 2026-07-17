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
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

CI 检测到 diff 中变更了 `README.md`，前一天的信息输出为：
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检逻辑）
- 失败原因: CI appstore 发布规范预检工具检测到 PR diff 中包含 `README.md` 的变更，但根级 `README.md` 文件的路径（`README.md`）与 appstore 发布规范要求的预期路径（`/README.md`）不匹配，导致校验失败。PR 本身为纯文档变更，仅更新了可用镜像 Tags 列表。

### 与 PR 变更的关联
PR 的改动仅为 `README.md` 和 `README.en.md` 的文本内容变更（新增 sp4、sp3、25.09、sp2 等 Tags 条目），无任何 Dockerfile、meta.yml、image-list.yml 等应用镜像构建相关的变更。CI appstore 发布规范预检对 diff 中的所有文件路径进行校验，根级 `README.md` 被纳入检查范围但路径格式不符合 appstore 预期（应为 `/README.md`），导致检查失败。此失败与 PR 的文档变更内容无关，属于 CI 校验逻辑对根级文件路径的处理问题。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 发布规范预检逻辑（`update.py`）在校验 diff 文件路径时，对根级 `README.md` 的路径表示（`README.md` vs `/README.md`）未做归一化处理。需在 CI 工具 `eulerpublisher` 中修正路径比对逻辑，使其在比较时对根级文件路径做归一化（统一添加或移除前导 `/`），避免因路径格式差异误报。

### 方向 2（置信度: 中）
由于本 PR 为纯文档变更且不涉及任何应用镜像的发布，CI 的 appstore 发布规范预检不应将根级 `README.md` 纳入检查范围。可在预检逻辑中增加对根级文档文件（`*.md` 位于仓库根目录）的豁免规则，使其跳过 appstore 路径校验。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径比对的具体实现逻辑，确认是字符串直接比较还是经过路径归一化处理。
- CI 预检是否有明确的文件白名单机制，根级 README 文件是否应被纳入 appstore 发布规范检查范围。

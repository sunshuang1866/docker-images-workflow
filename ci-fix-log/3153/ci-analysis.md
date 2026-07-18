# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范检查器对仓库根目录的 `README.md` 执行了路径校验，期望路径格式为 `/README.md`（绝对路径），但 diff 中检测到的变更文件路径为 `README.md`（相对路径），导致路径格式校验不通过。

### 与 PR 变更的关联
本次 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 中的文档内容——新增基础镜像可用 tag（`24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2`），并更新 `latest` tag 对应的链接。PR 的变更内容本身正确无误。CI 失败是因为 appstore 发布规范检查器对所有变更文件统一执行路径校验，但根目录的仓库级 README 文件不属于任何 appstore 镜像目录，不应受此路径规则约束。检查器未能区分仓库级文档和 appstore 镜像文档，将路径格式差异（`README.md` vs `/README.md`）误报为规范错误。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的 appstore 路径校验逻辑需要修正：应将仓库根目录文件（如根 `README.md`、`README.en.md`、`LICENSE` 等）从 appstore 发布规范的路径校验中排除，或在 diff 文件列表输入阶段对路径做归一化处理（统一补前导 `/`）。这不是 PR 作者能够修复的问题，需要 CI 维护方调整校验工具。

### 方向 2（置信度: 低）
如果 CI 工具期望 PR 作者以特定方式提交（如通过某种元数据声明跳过根级 README 的路径检查），PR 作者可能需要在上游 CI 文档中确认是否存在此类声明机制。但从当前日志和 diff 来看，本次 PR 无需也无法从 PR 侧修复。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 第 273 行前后完整的路径校验逻辑，确认是否有现成的白名单机制可以排除根级仓库文件。
- CI 工具维护方对仓库根级 README 文件的路径校验策略预期是什么——是否是一个已知的 CI 工具 bug，还是 PR 提交方式需要调整。

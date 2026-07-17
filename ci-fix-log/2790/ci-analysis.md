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
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 规范校验阶段）
- 失败原因: CI 的 appstore 发布规范预检脚本检测到 `README.md` 被修改，将其送入路径校验流程。该校验要求文件必须符合 appstore 镜像条目的路径层级规范（如 `分类/镜像名/版本/OS版本/文件`），而根目录下的 `README.md` 是项目文档而非镜像条目目录中的文件，无法通过 appstore 路径规范匹配，被判定为 "Path Error: The expected path should be /README.md"。

### 与 PR 变更的关联
PR 仅修改了 `README.md` 和 `README.en.md` 两个文档文件（更新支持的 Tags 列表，新增 25.09、24.03-lts-sp3、24.03-lts-sp2 条目，并将 latest 标签从 24.03-lts-sp2 改为 24.03-lts-sp3）。这些是纯文档变更，不涉及任何 Dockerfile 或镜像元数据。但 CI 的 appstore 预检工具将 `README.md` 纳入校验范围，导致文档变更被错误地按镜像条目路径规范进行校验而失败。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 预检工具对 diff 中所有文件（包括根目录文档）均执行路径校验。需要确认 `update.py` 中的校验逻辑是否正确过滤了根目录文档文件（如 `README.md`、`README.en.md`）。如果这是 CI 工具的设计意图（根目录文档变更应单独处理），则此 PR 的文档变更不应触发 appstore 路径校验；如果是 CI 工具 bug，则需修复 `update.py` 在校验前添加文件路径的过滤逻辑，排除非镜像条目目录下的文件。

### 方向 2（置信度: 低）
错误消息 "The expected path should be /README.md" 与文件实际路径（已经是 `/README.md`）完全一致，存在 CI 工具内部路径格式比较出错的可能性（如相对路径 `README.md` vs 绝对路径 `/README.md` 格式不匹配）。如果是此情况，属于 CI 工具实现缺陷，与 PR 代码无关。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的 appstore 校验逻辑：如何区分"镜像条目目录下的文件"与"根目录文档文件"。需要确认该校验是否本应过滤掉 `README.md`，还是根目录文档变更确实不允许出现在 PR 中。
2. 确认 CI 在 `README.md` 已位于正确路径 `/README.md` 的情况下仍报 "Path Error" 是否为一个已知的 CI 工具问题。
3. 历史 PR 中是否有纯文档变更（仅修改 README.md）通过此 CI 检查的先例，以判断这是 PR 改动引入的新问题还是 CI 工具长期存在的问题。

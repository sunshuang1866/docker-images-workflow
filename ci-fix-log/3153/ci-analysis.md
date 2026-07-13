# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）要求被修改的文件路径必须符合应用镜像发布规范（即文件应位于 `{category}/{app}/{version}/{os-version}/` 等标准镜像路径下），而本 PR 修改的两个文件 `README.en.md` 和 `README.md` 位于仓库根目录，不在任何应用镜像路径中，被路径校验拒绝。

### 与 PR 变更的关联
PR 的变更仅涉及 `README.en.md` 和 `README.md` 两个仓库根级文档文件的标签列表更新，属于纯文档修改。该 PR 不包含任何应用镜像 Dockerfile 或元数据文件的变更。CI 流水线的 appstore 预检步骤对所有 PR 强制执行路径校验，根级 README 文件不在白名单中，因此校验直接失败。**失败与 PR 文档内容的正确性无关，而是 CI 流水线对纯文档 PR 缺少路径豁免机制。**

## 修复方向

### 方向 1（置信度: 中）
此失败是 CI 流水线配置问题，而非代码问题。`eulerpublisher` 的 appstore 路径校验应针对包含应用镜像变更的 PR 执行，对仅修改根级文档（如 `README.md`、`README.en.md`）的 PR 应跳过该校验。需在 CI 流水线（Jenkins job 或 `update.py`）中增加变更文件类型的判断逻辑：若 PR 仅修改仓库根目录的文档文件，则跳过 appstore 路径校验步骤。

### 方向 2（置信度: 低）
如果 CI 流水线不允许跳过 appstore 校验，则需将根级 `README.md` 和 `README.en.md` 加入 `eulerpublisher` 的路径白名单中，使其通过校验。但这可能引入副作用（如允许将非应用镜像文件误上架到 appstore），需谨慎评估。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 附近的路径校验逻辑具体实现——需要查看源代码以确认白名单/黑名单机制和跳过条件。
2. 该 CI 流水线是否有针对纯文档 PR 的跳过逻辑或条件分支，目前从日志中无法确认。
3. 历史同类 PR（仅修改根级 README 的 PR）是否也遇到过同样的问题——用于判断这是新增问题还是已知行为。
4. `README.md` 自身路径即为 `/README.md`，为何仍被标记为 `[Path Error]`——可能该校验逻辑对所有非白名单文件统一输出相同错误描述，或校验逻辑中存在绝对路径/相对路径比较的 bug。

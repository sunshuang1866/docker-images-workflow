# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI路径校验误伤文档PR
- 新模式症状关键词: appstore, specification errors, README.md, Path Error, expected path

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布路径预检工具 (`update.py`) 对 PR 中变更的全部文件进行路径格式校验，要求文件路径遵循应用镜像目录结构（如 `Category/ImageName/Version/OS/Dockerfile`）。但 PR #3153 仅修改了仓库根目录的 `README.md` 和 `README.en.md`——这两个纯文档文件不属于任何应用镜像目录，也不遵循 appstore 的路径规范，因此校验失败。

### 与 PR 变更的关联
PR 变更内容为更新 `README.md` 和 `README.en.md` 中基础镜像的 Tags 列表（将 latest 从 24.03-lts-sp2 更新为 24.03-lts-sp4，并补充新增版本标签）。这是一个纯文档更新 PR（`docs:` 前缀），不涉及任何 Dockerfile 或应用镜像构建文件的修改。

CI 失败与 PR 的内容变更**无关**——README.md 和 README.en.md 本来就位于仓库根目录，PR 并未改变其路径。CI appstore 路径校验对所有 PR 一视同仁地执行，不具备对纯文档 PR 的豁免机制，导致误伤。

## 修复方向

### 方向 1（置信度: 中）
该 PR 因 CI appstore 路径校验误伤而失败，属于 CI 工具设计层面的边界情况。可行的处理方式包括：
- 确认该 CI 预检规则是否存在对根级文档文件（`README.md`、`README.en.md`）的豁免列表，如有则将该 PR 合并触发重检
- 若 CI 预检工具无豁免机制，需向 CI 维护团队反馈此问题，或可考虑通过关闭 appstore 预检触发条件来绕过（仅限文档类 PR）
- 另一个可能：PR 创建者使用的是 fork 分支 (`sunshuang1866:fix/3153`)，CI 预检在 clone PR 源仓库时路径解析可能与主仓库存在差异

### 方向 2（置信度: 低）
若 CI 日志中 `README.md` 的路径确实存在格式偏差（如 git diff 给出的路径缺少前导 `/`），可能是 CI 工具在路径标准化环节存在 bug，需检查 `update.py` 中的路径处理逻辑。

## 需要进一步确认的点
1. CI appstore 预检规则（`update.py:273`）是否有 root-level 文件（如 `README.md`、`README.en.md`）的白名单或豁免逻辑
2. 历史上同类纯文档 PR 是否也会触发此预检，以及它们是如何通过的
3. `eulerpublisher/update/container/app/update.py:222-273` 的路径校验逻辑，明确 `/README.md` 和 `README.md` 的差异来源

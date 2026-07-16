# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录README路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, eulerpublisher, appstore

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）检测到 PR 变更了仓库根目录的 `README.md`，并对其执行了镜像路径格式校验。校验逻辑期望文件路径以 `/` 开头（即 `/README.md`），而 diff 检测产出的路径为不含前导斜杠的 `README.md`，触发 `[Path Error]`。该 PR 仅修改了 README 文档中的基础镜像 tag 列表，属于纯文档更新，不应受 appstore 镜像路径规范的约束。

### 与 PR 变更的关联
- PR 变更内容：修改 `README.md` 和 `README.en.md` 中的基础镜像可用 tag 列表（更新 `latest` 从 lts-sp2 指向 lts-sp4，新增 sp2/sp3/25.09 条目）
- 失败与 PR **内容无关**：文档修改本身没有错误。CI 对所有变更文件无条件执行 appstore 路径格式检查，根目录 README 不符合镜像路径格式，但这是 CI 检查范围设计问题，非 PR 引入的代码缺陷
- 注意：CI 日志显示 `Difference` 仅检出 `README.md`，未检出 `README.en.md`，说明 diff 检测可能只取了变更文件的部分子集

## 修复方向

### 方向 1（置信度: 中）
CI appstore 发布规范预检不应将仓库根目录的纯文档文件（`README.md`、`README.en.md` 等）纳入镜像路径格式校验范围。需在 `eulerpublisher/update/container/app/update.py` 中增加文件过滤逻辑：跳过仓库根目录的非镜像相关文件（如 README.md、README.en.md、LICENSE 等），仅对实际位于场景目录（`AI/`、`Bigdata/`、`Cloud/` 等）下的文件执行路径格式检查。

### 方向 2（置信度: 低）
若 CI 工具本身允许根目录文件不参与路径校验，则可能是 `update.py` 生成 diff 路径时缺少前导 `/` 导致。需在 diff 路径产出阶段统一补上前导 `/`（如 `"/" + filepath`），但此方向仅为推测，证据不足。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的校验逻辑，确认是对所有变更文件无条件执行路径格式检查，还是已有过滤逻辑但未生效
2. `README.en.md` 同样被 PR 修改但未出现在 `Difference` 列表中——需确认 diff 检测是否仅报告了第一个文件，还是 `README.en.md` 被某条规则豁免（而 `README.md` 未被豁免）
3. 该 CI job 的触发条件：是否为所有 PR 均强制执行 appstore 发布规范校验？若为误触发，需调整 job 的 trigger 条件

## 修复验证要求
不适用。本失败为 infra-error，与 PR 代码变更无关，且修复方向指向 CI 工具自身逻辑调整，不涉及正则 patch 外部源文件。

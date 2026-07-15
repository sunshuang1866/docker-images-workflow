# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 部分匹配模式11（CI appstore 路径校验）
- 新模式标题: 纯文档变更触发发布校验
- 新模式症状关键词: Path Error, specifiication errors for releasing on appstore, README.md, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455 - INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具 appstore 发布规范校验）
- 失败原因: PR 仅包含根目录 `README.md` 和 `README.en.md` 的文档修改（更新支持的镜像 Tags 列表），不涉及任何应用镜像文件（Dockerfile、meta.yml、image-info.yml 等）。CI 流水线中的 `eulerpublisher` 工具在处理 merge_request 触发事件时，对所有变更文件执行 appstore 发布规范检查，该检查要求 PR 包含符合格式的应用镜像发布文件，纯文档变更不满足此要求，导致校验失败。错误消息 "The expected path should be /README.md" 可能表明 CI 工具内部路径归一化处理存在偏差（diff 输出 `README.md` 与预期 `/README.md` 的斜杠前缀匹配问题），或工具将根级 README 变更视为不满足发布规范的"异常路径"。

### 与 PR 变更的关联
**直接关联**。PR #2790 的 diff 仅包含以下变更：
- `README.md`：更新 "可用镜像的Tags" 表，将 latest 标签从 `24.03-lts-sp2` 改为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 标签行，修正 `24.03-lts-sp2` 对应的链接 URL（由错误的 `openEuler-24.03-LTS-SP1` 改为正确的版本 URL）
- `README.en.md`：同上内容的英文版更新

这些变更不涉及任何应用镜像目录 `{类别}/{镜像名}/{版本}/{OS版本}/` 下的 Dockerfile、meta.yml、image-info.yml 等文件。CI 的 appstore 发布规范校验器只识别到根级 README 变更，无法将其关联到任何有效的应用镜像发布单元，因此判定为校验失败。

## 修复方向

### 方向 1——若本 PR 仅为文档维护，则此为 CI 工具误报（置信度: 中）
如果 PR #2790 的意图是纯粹的文档更新（更新可用镜像 Tags 列表以反映最新发布状态），不涉及任何应用镜像的新增或修改，则 CI 流水线的 appstore 发布规范检查不应阻止此类 PR 合入。此场景下，该失败属于 CI 工具配置问题——`eulerpublisher` 的 merge_request 触发器可能未区分"纯文档变更"与"应用镜像发布"，将所有 PR 都纳入了 appstore 校验流程。

可能的解决思路：在 CI 触发器或校验逻辑中增加判断，当 PR diff 中仅包含根级文档文件（`README.md`、`README.en.md`、`.claude/README.md` 等）且不含任何应用镜像目录文件时，跳过 appstore 发布规范检查。

### 方向 2——若 PR 本应包含应用镜像变更（置信度: 低）
如果 PR 编号 2790 对应一个 issue/fix 分支本应同时包含应用镜像变更（如新增 `25.09` 或 `24.03-lts-sp3` 版本的某应用镜像 Dockerfile），但当前 PR 遗漏了这些文件，则 CI 校验失败是预期行为。此时需在 PR 中补充对应的应用镜像文件（Dockerfile、meta.yml、image-info.yml 等）。

但从 diff 内容来看，PR 仅修改了两个 README 文件的 Tags 列表，缺乏任何应用镜像目录的痕迹，此方向概率较低。

## 需要进一步确认的点
1. PR #2790 的实际意图：仅更新 README 中的 Tags 列表，还是本应伴随应用镜像变更？
2. CI 工具 `eulerpublisher/update/container/app/update.py:273` 的具体校验逻辑：路径比对是精确字符串匹配还是归一化比较？`README.md` 与 `/README.md` 的差异是因归一化缺失还是其他原因？
3. 该 CI 流水线是否曾正确处理过仅含根级文档变更的 PR（如仅修改 `README.md` 或 `.claude/README.md` 的历史 PR）？可查询本地 CI 日志或校验规则判断历史行为。
4. 若确认此为文档维护 PR 且应豁免 appstore 校验，需确认在 CI 编排层（Jenkins pipeline 配置）中如何为纯文档变更添加跳过条件。

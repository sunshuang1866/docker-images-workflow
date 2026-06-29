# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:37,042-...update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-29 15:21:41,552-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 流水线中的 appstore 发布规范预检脚本）
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）对所有变更文件执行路径校验。PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），这两个根级文档文件不属于任何 appstore 发布条目路径模板，因此校验失败，报 `[Path Error] The expected path should be /README.md`。

### 与 PR 变更的关联
**与 PR 内容无关**。PR 的变更仅限更新 README.md/README.en.md 中的镜像 Tag 列表（新增 `24.03-lts-sp3`、`25.09` 等条目，修正链接指向），属于纯粹的文档维护操作。失败由 CI 流水线中的 appstore 预检步骤错误地将根级文档文件纳入发布规范校验范围所致，而非 PR 的改动内容有误。CI 预检在设计上未区分"应用镜像发布变更"与"仓库文档变更"，导致文档类 PR 被误拦截。

## 修复方向

### 方向 1（置信度: 中）
CI 方的 `update.py` 预检逻辑应增加文件过滤，对于在仓库根目录的纯文档文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等）跳过 appstore 发布规范校验，不将其视为发布候选条目。这需要修改 CI 侧的 eulerpublisher 代码（`update.py` 在差异枚举之后、校验之前增加路径过滤逻辑）。

### 方向 2（置信度: 低）
若 CI 流水线有基于触发条件的区分机制（如仅当 PR 包含特定目录变更时才触发 appstore 预检），可调整触发规则，使得仅变更根级 `*.md` 文件的 PR 不触发 appstore 校验。

## 需要进一步确认的点
1. CI 流水线中 `update.py` 的完整校验逻辑——该脚本如何区分"应用镜像发布 PR"和"仓库文档维护 PR"。
2. 仓库根级 `README.md` 和 `README.en.md` 是否在 `image-list.yml` 中有条目（预期不应有），确认其被纳入校验范围的原因。
3. 此 CI 预检是否为本次流水线新增的校验步骤，还是已有步骤因 PR #2790 的变更类型而首次触发失败。

## 修复验证要求
本报告判定为 infra-error，修复需在 CI 流水线侧（`eulerpublisher/update/container/app/update.py`）进行，不涉及 PR 代码变更。code-fixer 若需介入，应：
1. 获取 `eulerpublisher` 仓库中 `update.py` 的完整源码，确认差异枚举和校验逻辑的具体实现。
2. 验证在枚举差异阶段或校验阶段添加根级文件过滤后，纯文档 PR 不再被 appstore 预检拦截。

# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验步骤）
- 失败原因: CI 的 appstore 发布规范校验器检查了 PR 变更文件列表，发现修改了根目录下的 `README.md` 和 `README.en.md`。校验器判定这两个文件不符合 appstore 发布规范中定义的预期文件路径（规范中的路径模式预期的是应用镜像目录结构如 `{Category}/{ImageName}/{Version}/{OSVersion}/Dockerfile`），根级 README 文件不在允许变更的路径范围内，因此报 `[Path Error]`。

### 与 PR 变更的关联
PR #2790 仅修改了根目录下两个 README 文件（`README.md` 和 `README.en.md`），更新了基础镜像的 Tags 列表（将 latest 从 24.03-lts-sp2 更新到 24.03-lts-sp3，并新增 25.09 和 24.03-lts-sp2 条目）。这些变更属于纯文档更新，不涉及任何应用镜像 Dockerfile 的新增或修改。

CI 流水线中的 appstore 发布规范校验步骤（`update.py:273`）在上游 x86-64 构建 job 中运行，其职责是检查 PR 中的文件变更是否符合应用镜像上架规范。由于 PR 仅修改了根级文档文件，不满足规范预期的路径模式（规范期望变更文件位于 `{Category}/.../Dockerfile` 结构下），校验器将其标记为路径错误。

## 修复方向

### 方向 1（置信度: 高）
该失败是 CI 规范校验与 PR 变更内容类型不匹配导致的问题。PR 是对根级 README 的纯文档更新，不应进入 appstore 发布规范的路径校验流程。这是一个 CI 流程设计问题——根级文档变更不应被 appstore 校验器拦截。建议在 CI 校验器中增加对根级纯文档文件（`README.md`、`README.en.md` 等）的豁免逻辑。

### 方向 2（置信度: 中）
如果项目规范要求所有 PR 必须包含应用镜像的变更（i.e. 不允许纯文档 PR），则此失败是预期行为。这种情况下 PR 需要补充实际的应用镜像 Dockerfile 变更，或将文档更新附加到其他功能性 PR 中。

## 需要进一步确认的点
1. 确认该 CI 校验器（`eulerpublisher/update/container/app/update.py`）的路径校验逻辑：根级 `README.md` / `README.en.md` 是否预期被校验规则豁免？还是说所有通过该 job 的 PR 变更都会经过此校验？
2. 确认根级 README 的文档更新是否预期被 appstore 校验步骤拦截，或者这属于 CI 流程配置偏差（如上游 trigger job 错误地将文档 PR 路由到了应用镜像构建流水线）。

## 修复验证要求
（不适用——当前分析不涉及正则 patch 外部源文件）

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
2026-06-29 15:21:41,552-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 流水线 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范预检对 PR 中所有变更文件进行路径校验，要求文件位于符合规范的镜像目录路径下（如 `{场景}/{镜像名}/{版本}/{系统版本}/`）。PR #2790 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个文档文件，它们不在任何镜像目录路径内，被预检判定为 `[Path Error]`。

### 与 PR 变更的关联
PR #2790 的改动仅限于 `README.md` 和 `README.en.md`，内容为更新基础镜像支持 Tags 列表（新增 `24.03-lts-sp3`、`25.09` 条目，修正 `latest` tag 的链接）。无任何 Dockerfile 变更或新镜像提交。CI 的 appstore 预检未对纯文档类 PR 做豁免处理，导致此 PR 被误判。同类问题在 PR #2512 中出现过（`.claude/` 目录下的 README 文件被路径校验拦截）。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线的 pre-check 逻辑（`update.py`）需区分"新增/修改镜像文件"和"纯文档/仓库维护类变更"。对于仅涉及仓库根目录 README、`.claude/` 等非镜像目录文件的 PR，应跳过 appstore 路径校验。此修改需在 CI 流水线层面完成，不在本仓库 Dockerfile 范围内。

## 需要进一步确认的点
1. 此仓库的 CI 触发热文件检测策略是什么——是否允许纯文档 PR 合并而无需触发 appstore 校验？
2. `update.py` 中是否有白名单机制可以排除根目录 README 等非镜像文件？若有，需确认是否将其添加到白名单。
3. 若此次 CI 失败是预期行为（即要求所有 PR 都必须包含至少一个镜像变更），则 PR 提交者需了解此规则。

## 修复验证要求
(不适用 — 修复涉及 CI 流水线逻辑变更，非代码仓库内容修改)

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
2026-07-12 15:33:13,075-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273` (appstore 发布规范预检)
- 失败原因: CI appstore 发布规范预检工具对 PR 变更的两个根目录文件 `README.md` 和 `README.en.md` 执行路径校验。对于 `README.en.md`，实际路径 `/README.en.md` 与期望路径 `/README.md` 不匹配；对于 `README.md`，虽然实际路径 `/README.md` 与期望路径 `/README.md` 表面一致，但预检工具仍标记为 `[Path Error]`（可能因为根目录文件不属于 appstore 管理的镜像目录结构，被整体拒绝）。PR 仅修改了根目录 README 文档（更新基础镜像可用 tag 列表），不涉及任何 Dockerfile 或镜像发布文件。

### 与 PR 变更的关联
PR 直接修改了根目录 `README.md` 和 `README.en.md`，触发了 CI appstore 发布规范预检。该预检流程设计目标是校验应用镜像发布文件的路径规范，不应拦截纯文档变更。失败与 PR 的代码内容无关，属于 CI 流程对文档类 PR 的过度拦截。

## 修复方向

### 方向 1（置信度: 中）
在 CI 预检工具 `update.py` 中为根目录文件（如 `README.md`、`README.en.md`）添加白名单或免检逻辑。纯文档类 PR 不应受 appstore 发布路径规范约束。参考历史模式 11 中类似案例，路径校验范围应限定在应用镜像目录（`AI/`、`Bigdata/`、`Database/` 等）内。

### 方向 2（置信度: 中）
若 CI 策略不允许直接绕过根目录文件的检查，可将 `README.md` 和 `README.en.md` 的变更合并到包含实际镜像变更的 PR 中提交，或通过其他渠道（如 Wiki）更新基础镜像 tag 文档。当前 PR 的 diff 仅涉及 README 更新，可通过 CI 旁路合并。

## 需要进一步确认的点
1. `update.py:273` 的完整路径校验逻辑——`README.md` 在路径 `/README.md` 与期望完全一致的情况下为何仍被标记失败（可能根目录文件被整体拒绝，或有隐藏的额外校验条件如内容格式检查）
2. CI 系统是否提供纯文档变更的免检机制（如 `[skip ci]` 标签、特定文件白名单）
3. PR 分支名 `fix-upstream-version-detection` 与 diff 内容（仅 README 更新）不一致——需确认该 PR 是否遗漏了实际的代码修复变更

## 修复验证要求
不涉及代码修复。若方向 1 被采纳，修改 CI 预检工具后需验证一个纯 README 变更的 PR 能正常通过。

# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11

## 根因分析

### 直接错误
```
| .claude/agents/README.md | [Path Error] The expected path should be .claude/README.md |   FAILURE    |
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `.claude/agents/README.md`
- 失败原因: CI appstore 发布规范预检要求工具目录 `.claude/` 下的 README 文件位于 `.claude/README.md`（根层级），而非嵌套在 `agents/` 子目录下的 `.claude/agents/README.md`

### 与 PR 变更的关联
本次 PR 将工具目录整体从 `.agents/` 迁移到 `.claude/`。原 `.agents/agents/README.md` 被重命名为 `.claude/agents/README.md`（路径中 `agents/` 子目录层级被保留）。CI 的 appstore 发布规范检查对 `.claude/` 工具目录的 README 路径有严格校验：README 必须直接位于 `.claude/` 根下（即 `.claude/README.md`），不允许嵌套在 `agents/` 子目录中。PR 触发此校验后失败。

## 修复方向

### 方向 1（置信度: 高）
将 README 文件从 `.claude/agents/README.md` 移动到 `.claude/README.md`，使其符合 CI appstore 发布规范的路径要求。如果 `agents/` 目录下的 README 内容主要描述 agents 机制本身，可考虑将其合并到 `.claude/CLAUDE.md` 或 `.claude/README.md` 中。

### 方向 2（置信度: 中）
如果 `.claude/agents/README.md` 的内容仅对 agents 子目录有说明价值、不应放在 `.claude/` 根层级，则需要确认 CI 的 appstore 路径校验规则是否可配置，或是否应将此文件从 PR 变更范围中排除（不作为 appstore 发布需要校验的文件）。

## 需要进一步确认的点
- `.claude/CLAUDE.md`（由 `.agents/CLAUDE.md` 重命名而来）是否也需要通过 appstore 路径校验，以及其期望路径是什么
- CI appstore 路径校验规则的具体实现逻辑：是否有文件白名单机制允许 `.claude/agents/` 下的非应用镜像文件被豁免检查

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
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检工具）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）在检查 PR 变更文件路径时存在路径格式比较缺陷——`git diff --name-only` 输出相对路径 `README.md`（无前导 `/`），而工具期望绝对路径 `/README.md`（有前导 `/`），导致字符串比较不匹配，判定为 "Path Error"。该 PR 仅在仓库根层级修改了两个 README 文档文件（`README.md` 和 `README.en.md`），未涉及任何 Dockerfile 或镜像元数据变更，该 CI 检查本不应被触发或不应作为阻塞项。

### 与 PR 变更的关联
PR 变更**与此次 CI 失败无直接因果关系**。PR 仅更新了 `README.md` 和 `README.en.md` 中基础镜像可用 tags 的文档信息（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，调整展示顺序）。没有任何 Dockerfile、`meta.yml`、`image-info.yml` 或 `image-list.yml` 被修改。CI 失败根因是 appstore 预检工具在处理 `git diff` 输出的文件路径时未做路径规范化（缺少前导 `/`），属于 CI 基础设施层面的缺陷。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施维护者修复 eulerpublisher 的 `update.py` 中的路径比较逻辑，在 diff 文件列表与预期路径做匹配前，统一添加前导 `/` 或统一去除前导 `/` 进行规范化比较。Code Fixer 无需处理，与 PR 代码无关。

### 方向 2（置信度: 低）
若该 CI 检查对纯文档 PR 本不应触发，CI 流水线配置层面需添加过滤逻辑：当 PR 变更文件仅为根目录下的 `README.md`、`README.en.md` 等纯文档文件时，跳过 appstore 发布规范预检步骤。

## 需要进一步确认的点
1. 确认 eulerpublisher `update.py` 中路径比较逻辑的具体实现，验证是否为绝对路径 vs 相对路径的字符串比较问题。
2. 确认同一仓库中其他仅修改根目录 README 文件的历史 PR 是否也触发了同样的 CI 失败（若历史 PR 通过，则本次失败可能另有原因，证据不足）。
3. 确认 CI appstore 预检步骤是否对纯文档变更 PR 设计为放行——若设计如此但实际被触发，则属于 CI 流水线配置缺陷。

## 修复验证要求
（不适用——本次失败为 infra-error，根因在 CI 工具路径处理逻辑，与 PR 代码变更无关，Code Fixer 无需提交代码修复。）

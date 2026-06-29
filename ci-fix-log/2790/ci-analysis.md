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
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: CI 流水线中 `eulerpublisher/update/container/app/update.py:273` 的 appstore 发布规范校验阶段
- 失败原因: 该 PR 仅修改了仓库根目录下的 `README.en.md` 和 `README.md` 两个文档文件（更新 Tags 列表），未包含任何 Dockerfile 或镜像元数据变更。CI 的 appstore 发布规范校验工具将此 PR 解释为一次镜像发布提交流程，但两个 README 文件均不在预期的镜像目录结构（如 `{场景}/{应用名}/{版本}/{os-版本}/Dockerfile`）下，校验工具将其标记为 `[Path Error]`，导致流水线失败。

### 与 PR 变更的关联
PR 的改动直接触发了失败——校验工具通过 `git diff` 识别出 `README.en.md` 和 `README.md` 为变更文件，然后对其执行 appstore 发布路径规范检查。由于这两个文件是仓库根级文档而非 image 目录下的文件，校验无法通过。**问题不在 PR 改动内容本身（文档更新正确），而在 CI 流水线未对纯文档类型 PR 做豁免处理。**

## 修复方向

### 方向 1（置信度: 中）
在 CI 的 `update.py` 校验逻辑中增加对纯文档变更的豁免：当 `git diff` 中所有变更文件的路径前缀均不与 `image-list.yml` 中任何镜像目录匹配，且不含 `Dockerfile` / `meta.yml` 等构建相关文件时，跳过 appstore 发布规范检查，直接放行。此修改属于 CI 流水线层面的改进，Code Fixer 无需处理。

### 方向 2（置信度: 低）
如果项目要求 README 变更也必须走 appstore 发布流程，则需要在与该 PR 关联的 `image-list.yml` 或等价元数据中为根级 README 文件注册合法的路径映射条目。但此方向与 README 文件在 repo 中的实际用途（项目级文档说明，非镜像发布描述文件）冲突较多，不推荐。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑：它是否要求所有变更文件都必须属于某个已知镜像目录？是否已有针对非 Dockerfile 文件的豁免分支？
2. 该 CI 流水线是否被设计为所有 PR（包括纯文档 PR）都必须经过 appstore 规范检查？如果是，确认是设计意图还是流水线配置错误。
3. 历史上是否有纯 README/Documentation PR 通过该 CI 检查的成功案例，以排除这是新引入的回归。

## 修复验证要求
无需填写——此失败属于 CI 流水线工具逻辑问题，不涉及 Dockerfile 代码修复或正则 patch 操作。Code Fixer 无需处理此 PR。

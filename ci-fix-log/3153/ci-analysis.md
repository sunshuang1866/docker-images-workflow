# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 脚本 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检脚本对仓库根目录的 `README.md` 执行了路径校验，判定 `README.md` 不满足期望路径 `/README.md`。但 `README.md` 是仓库级文档而非应用镜像级文件，此路径校验属于 CI 工具误报。

### 与 PR 变更的关联
**与 PR 变更无关**。PR #3153 仅为文档变更——更新 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 条目，修正旧条目的链接）。未新增任何镜像目录、Dockerfile 或元数据文件。CI 工具 `update.py` 检测到 `README.md` 被修改后将其纳入 appstore 路径校验，但仓库根目录的 README 不应受此校验约束。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，PR 代码本身无误。需由 CI/平台维护者更新 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑，将仓库根目录的 `README.md`、`README.en.md` 等顶层文档文件排除在 appstore 发布规格检查范围之外。

### 方向 2（置信度: 低）
如果 CI 校验逻辑是故意设计为检查所有 README 文件的路径格式，则问题在于本次 PR 修改了根 `README.md` 但该文件不满足路径格式要求。但考虑到根 README 是仓库级文档而非应用镜像文件，此场景可能性很低。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑——确定其对仓库根目录文件的处理策略是设计意图还是遗漏
2. CI 流水线中 trigger job 与下游 x86-64 构建 job 的完整日志——当前日志仅来自 x86-64 构建节点上的 appstore 预检步骤，确认是否还有其他下游 job 失败
3. 该 CI 预检步骤是否在近期有过逻辑变更，导致此前相同的根 README 变更未触发此错误

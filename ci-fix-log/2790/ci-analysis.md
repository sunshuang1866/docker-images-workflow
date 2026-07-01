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
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: PR 仅修改了仓库根目录下的 `README.en.md` 和 `README.md`（文档内容更新，新增/调整支持的镜像 Tags 条目），CI 的 appstore 发布规范检查工具 `update.py` 对变更文件进行路径校验，发现这两个文件不满足 appstore 发布所需的 `{category}/{image}/{version}/{os-version}/Dockerfile` 层级结构，两个文件均被判定为路径不符规范而报 FAILURE。

### 与 PR 变更的关联
PR 变更直接触发了此失败。diff 中仅包含 `README.en.md` 和 `README.md` 的文档内容修改（更新 `24.03-lts-sp2` → `24.03-lts-sp3` 的链接、新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` Tags 条目），无任何 Dockerfile 或镜像构建文件变更。CI 流水线被 merge_request 事件触发后，appstore 规范预检步骤扫描 diff 文件列表，发现变更内容全部为根目录 README 文件，不符合应用镜像发布的路径规范，因此报错。

## 修复方向

### 方向 1（置信度: 高）
这是一个纯文档 PR，变更内容本身是合法的 README 维护工作。CI 失败是因为流水线的 appstore 发布规范检查默认要求 PR 变更必须包含符合 `{category}/{image}/{version}/{os-version}/` 结构的 Docker 镜像文件。如果本 PR 的意图仅为更新 README 文档，无需修复——此 CI 失败是流水线对文档类变更的预期行为，可忽略。

### 方向 2（置信度: 中）
如果本 PR 必须通过 CI（如分支保护规则要求），则需要为 PR 补充至少一条符合 appstore 发布规范的 Docker 镜像变更（如新增一个 Dockerfile 或修改已有镜像文件），使 CI 检查有合法目标可校验。

## 需要进一步确认的点
- 确认 PR #2790 的合并策略：是否允许跳过 CI 检查（如使用 `/approve` 或 admin merge）来处理纯文档 PR
- 确认 CI 流水线是否有配置项可针对仅含文档变更的 PR 跳过 appstore 规范预检步骤

## 修复验证要求
无需验证（本 PR 为纯文档变更，修复方向 1 建议直接忽略 CI 失败）。

# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR触发发布检查
- 新模式症状关键词: Path Error, expected path, /README.md, appstore, specification errors, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-...update.py[line:356]-INFO: Difference: [
    "README.md"
]
Cloning into '/tmp/eulerpublisher_v59dw93p/ci/container/check/****-docker-images'...
2026-07-14 15:28:07,677-...update.py[line:222]-INFO: Clone ... successfully.
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI `eulerpublisher` appstore 发布规范检查阶段（`update.py:273`），检查对象为仓库根目录的 `README.md`
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 变更了 `README.md`，但该文件位于仓库根目录（`/README.md`），不符合 appstore 镜像发布所需的目录结构（应为 `{image-name}/{version}/{os-version}/README.md` 形式），检查工具将其判定为路径错误

### 与 PR 变更的关联
PR #2790 **仅修改了文档文件**——`README.md` 和 `README.en.md`，内容是更新基础镜像的 Supported Tags 列表（修正 SP2→SP3 的链接错误、新增 25.09 标签、补充 sp3/sp2 条目）。PR 未包含任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关变更。

CI 流水线对所有 PR 统一执行 appstore 发布规范预检，当检测到变更文件为根目录 `README.md` 时，该工具无法将其映射到任何合法的 appstore 镜像发布路径（如 `AI/{image}/{version}/{os-version}/Dockerfile`），因此报"Path Error"并标记构建失败。

**该失败与 PR 的文档内容质量无关**（文档变更本身正确），属于 CI 检查工具对文档类 PR 的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线应在 appstore 发布规范预检阶段增加过滤逻辑：当 PR 仅变更根目录级的项目文档（`README.md`、`README.en.md`、`LICENSE` 等非镜像文件）时，跳过该检查步骤。这需要修改 CI 编排脚本（Jenkins pipeline 或 `eulerpublisher` 工具），而非修改 PR 本身。

### 方向 2（置信度: 低）
如果 CI 流水线设计上要求所有 PR 都必须通过 appstore 预检，则文档类 PR 可考虑将 `README.md` 变更拆分为独立 PR，并使用 CI skip 标记（如 `[ci skip]`）跳过不必要的检查步骤。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中 `[Path Error]` 的具体判断逻辑：是什么条件导致根目录 `README.md` 被判定为路径错误？是该检查期望所有变更文件都符合 `{image-name}/{version}/{os-version}/` 层级，还是有其他验证条件？
- CI 流水线（trigger job）是否支持按变更文件类型跳过 appstore 预检步骤
- 该仓库是否允许纯文档 PR 不带任何应用镜像变更直接合入

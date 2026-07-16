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
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 修改了仓库根目录的 `README.md`，将其纳入 appstore 镜像发布路径校验，但根目录 `README.md` 是仓库级文档而非 appstore 镜像文件，不符合 `{image-version}/{os-version}/Dockerfile` 的 appstore 路径规范，导致路径校验失败。

### 与 PR 变更的关联
PR #2790 仅修改了两个根目录文档文件（`README.md` 和 `README.en.md`），更新了 openEuler 基础镜像的可用 Tags 列表。这两个文件均位于仓库根目录 `/` 下，是仓库级别的说明文档，与任何 appstore 应用镜像发布无关。CI 的 `eulerpublisher` 工具在 `git diff` 中检测到 `README.md` 变更后，不对变更文件类型/所在目录做区分，统一执行 appstore 发布规范校验，导致根目录文档被误判为不合规。

此失败与 PR 的具体改动内容无关——即使只修改 README 中的一个字符，也会触发相同的校验失败。

## 修复方向

### 方向 1（置信度: 高）
CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）应将仓库根目录文件（如 `README.md`、`README.en.md`）排除在 appstore 镜像路径校验之外。这类根目录文档不遵循 `{image-version}/{os-version}/Dockerfile` 的镜像文件路径规范，不应被纳入 appstore 规范检查范围。这是 CI 工具侧的缺陷，与 PR 代码变更无关。

### 方向 2（置信度: 高）
如果 CI 工具无法快速修改，PR 作者可以将 `README.md` 和 `README.en.md` 的修改拆分到独立 PR 中，该 PR 的 CI 流程跳过后处理阶段的 appstore 校验步骤（若 CI 提供了跳过标记）。但这是权宜之计，长期仍应在 CI 工具侧修复。

## 需要进一步确认的点
- 确认 `eulerpublisher` 工具中 `update.py` 的变更检测逻辑（`line:356` 附近 `Difference` 计算逻辑），是否检查了文件路径前缀过滤（如排除以根目录 `/` 开始的非镜像路径）
- 确认 CI pipeline 配置中是否支持按文件变更类型跳过 appstore 校验 stage（例如仅当变更涉及 `Bigdata/`、`AI/`、`Database/` 等场景目录时才触发校验）

## 修复验证要求
(不适用——此失败为 CI 工具缺陷，PR 代码本身无需修改，因此无需 code-fixer 执行验证步骤。)

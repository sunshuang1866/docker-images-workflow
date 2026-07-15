# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-/.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检对仓库根目录的 `README.md` 执行了路径校验，要求路径格式为 `/README.md`，但变更检测返回的路径为 `README.md`（无前导 `/`），路径字符串比较不匹配导致检查失败。该预检本应仅针对应用镜像目录（`{category}/{app}/{version}/{os-version}/`）下的文件执行，不应作用于仓库根级别的纯文档文件。

### 与 PR 变更的关联
**该失败与 PR 的改动无代码逻辑层面的关联**。PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md` 两个文件，内容是更新基础镜像可用 Tag 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，修正 past/latest 所指版本）。PR 不涉及任何 Dockerfile、`meta.yml`、`image-info.yml` 或 `image-list.yml` 的变更，纯属文档维护性提交。

CI 流水线中的 appstore 发布规范预检（`update.py`）根据 git diff 检测到 `README.md` 发生变更后，自动对该文件执行路径格式校验，而该文件作为仓库根层级的说明文档，不属于任何应用镜像的最小目录单元，不适用 appstore 路径规范。CI 预检未区分"应用镜像目录内的 README"和"仓库根目录的 README"，属于 CI 工具侧的逻辑缺陷。

## 修复方向

### 方向 1（置信度: 高）
**CI 流水线侧修复**：在 `eulerpublisher/update/container/app/update.py` 的变更文件过滤逻辑中，增加对仓库根目录文件（`README.md`、`README.en.md`、`.gitignore` 等非应用镜像目录下的文件）的豁免规则，使 appstore 发布规范预检仅在检测到 `{category}/{app}/` 路径下的文件变更时才触发路径格式校验。或者，修复路径比较逻辑中的前导 `/` 规范化问题（确保 `README.md` 与 `/README.md` 在语义上被视为等同）。

### 方向 2（置信度: 低）
**绕过方案**：如果 CI 工具的变更检测触发逻辑难以修改，可在 PR 工作流中增加策略——当 PR 仅包含根目录文档文件变更时，跳过 appstore 规范预检步骤。但这属于临时方案，不如方向 1 从工具侧根除问题。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑具体实现（`[Path Error] The expected path should be /README.md` 的触发条件），确认是路径前缀规范化问题还是文件豁免逻辑缺失。
2. CI 流水线是否有"纯文档 PR 跳过 appstore 检查"的策略配置项，若已有该配置，确认 PR 为何未被正确识别为纯文档变更。
3. 历史 `模式11` 中记录的多起 `.claude/README.md` 和 `.claude/agents/README.md` 路径校验失败案例是否与本次根因相同，以确认这是一个已知但未彻底修复的 CI 工具缺陷。

## 修复验证要求
此报告判定为 `infra-error`，修复应在 CI 工具代码（`eulerpublisher`）中进行，不涉及本仓库中任何 Dockerfile 或元数据文件的修改。修复后需验证：
- 对仅修改仓库根层 README 的 PR，appstore 预检步骤应自动跳过（或通过），不再报告路径格式错误。
- 对实际新增/修改应用镜像（含应用目录内 README.md）的 PR，路径校验仍需正常执行，确保回归防护不受影响。

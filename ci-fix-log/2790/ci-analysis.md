# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根文档路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, eulerpublisher, appstore

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具，非 PR 代码）
- 失败原因: CI appstore 发布规范预检工具检测到 PR 修改了根目录下的 `README.md`，对该文件执行了路径校验，判定其不符合 appstore 镜像提交的路径规范。`README.md` 是仓库根级文档文件，不属于任何镜像提交的 `{image-name}/{version}/{os-version}/Dockerfile` 结构，因此被路径校验规则拒绝。

### 与 PR 变更的关联
PR 变更内容仅为更新 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表——将"24.03-lts-sp2, 24.03, latest"的链接从已过时的 SP1 仓库 URL 更正为 SP3 仓库 URL，并补充和重新整理了多个 Tags 条目。这是一次纯粹的文档修正，不涉及任何 Dockerfile、meta.yml、image-list.yml 等镜像构建与发布的实质性变更。CI 失败是 appstore 校验工具对根级文档文件执行了不应适用的镜像路径检查所导致的**误报（false positive）**，与 PR 改动本身的正确性无关。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线中的 `eulerpublisher` appstore 规范预检环节应排除根级仓库文档文件（如 `/README.md`、`/README.en.md`、`/CONTRIBUTING.md` 等），仅对镜像提交相关文件（Dockerfile、meta.yml、image-info.yml、image-list.yml）执行路径校验。此修复在 CI 工具或流水线层面进行，不涉及本 PR 的代码修改。

### 方向 2（置信度: 低）
PR 自身作为纯文档修正 PR，CI 触发层可能无需启动 appstore 发布规范检查 job。如果流水线能在触发阶段识别 PR 仅包含文档文件变更（而不含 Dockerfile 等镜像文件），可直接跳过 appstore 检查，从源头避免误报。此方向依赖于 CI 编排层的能力，需要确认是否已有类似判别逻辑。

## 需要进一步确认的点
1. 日志中 `Difference: ["README.md"]` 仅列出了 `README.md`，但 PR diff 同时修改了 `README.en.md`，需确认为何 `README.en.md` 未被差异检测捕获——这可能是 `eulerpublisher` 工具只检查特定文件列表的结果，也可能是 Diff 提取逻辑有过滤条件。
2. 需在代码库中查阅 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑（约 273 行附近的 check 函数），确认其对根级文件的处理方式，以便准确判断是工具缺陷还是预期行为。
3. 确认本仓库的 appstore 发布规范中是否对根级 `README.md` 有明确的路径定位预期——若规范确实要求根级 README 不被纳入镜像路径检查，则此失败确实是 CI 工具 bug。

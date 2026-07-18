# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根文档触发appstore路径校验
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范检查阶段）
- 失败原因: PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（更新"可用镜像的Tags"文档），但 CI 的 appstore 发布规范检查器（eulerpublisher update.py）将变更文件 `README.md` 纳入了 appstore 镜像路径校验流程。根目录 `README.md` 不符合 appstore 镜像目录结构（期望在 `{category}/{image}/{version}/{os}/` 类路径下的 README.md），导致检查失败。本次 PR 不涉及任何镜像目录的 Dockerfile/appstore 发布内容，属于 CI 检查器对纯文档变更 PR 产生了误报。

### 与 PR 变更的关联
PR 的 diff 变动仅涉及两处文档内容：
1. `README.md` 第 22-25 行：更新可用镜像标签列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签条目）
2. `README.en.md` 第 23-26 行：同上（英文版同步更新）

PR 本身是为了修正 README 中过时的基础镜像标签信息，不包含任何 Dockerfile、meta.yml、image-list.yml 等与镜像构建或 appstore 发布相关的文件变更。CI 失败不是因为 PR 改动有误，而是 CI 检查器将根目录文档变更误判为 appstore 发布内容进行校验。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 规范检查器（`eulerpublisher/update/container/app/update.py`）在检测变更文件列表（line 356 输出 `Difference: ["README.md"]`）后，对所有被修改的 `README.md` 无条件执行 appstore 路径校验。应调整检查逻辑：当变更文件为仓库根目录文档（`/README.md` 或 `/README.en.md`）时，跳过 appstore 发布规范检查，因为根目录 README 属于仓库通用文档，不属于任何应用镜像的发布内容。

### 方向 2（可选，置信度: 低）
若 CI 检查器的路径校验逻辑要求所有 `.md` 文件必须位于镜像目录结构内，可考虑将本次根目录 README 的标签文档更新拆分为独立的非 appstore PR 工作流，或通过 CI 配置项将该 PR 标记为文档变更以绕过镜像路径校验。

## 需要进一步确认的点
1. 日志中 CI 运行信息显示 `PR 3184 [sunshuang1866:fix/3153 -> master]`，而当前诊断的是 PR #3153。需确认提供的日志是否确实是 PR #3153 的直接 CI 运行记录，还是来自一个修复 PR #3184 的间接 CI 运行。
2. 日志仅展示了 `x86-64` 架构构建 job 的输出。需确认 `aarch64` 等同级架构构建 job 是否也有相同或不同的失败信息。
3. `eulerpublisher/update/container/app/update.py` 第 222-273 行的 appstore 路径校验逻辑的具体实现——确认 `Difference: ["README.md"]` 检测与 path check 之间的映射关系，验证"纯文档变更触发误报"的推断是否正确。
4. 确认 CI 工作流中是否存在"仅文档变更应跳过 appstore 检查"的配置选项或分支逻辑。

## 修复验证要求
若修复方向为调整 `update.py` 中检查逻辑，code-fixer 必须在修改前：
1. 完整阅读 `eulerpublisher/update/container/app/update.py` 中第 200-280 行的变更检测与路径校验逻辑。
2. 确认 `Difference` 检测（line 356）如何将变更文件列表传递给 path check（line 273），以及是否存在已有的过滤条件（如仅检查特定后缀或目录的文件）。
3. 验证修改后，一个仅包含根目录 README.md 变更的 PR 不再触发 appstore 路径校验失败，同时包含镜像目录文件变更的 PR 仍能正常通过校验。

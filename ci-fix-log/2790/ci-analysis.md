# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径校验误判
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具内部校验逻辑）
- 失败原因: CI 的 appstore 发布规范预检工具对仓库根目录的 `README.md` 文件进行路径校验时，判定其路径不符合预期 `/README.md`。但 PR 修改的 `README.md` 确实位于仓库根目录，与期望路径一致，该错误很可能是 CI 工具路径比对逻辑的误判。

### 与 PR 变更的关联
PR 改动**仅限**仓库根目录下的两个 README 文件（`README.md` 和 `README.en.md`），内容为更新可用镜像 Tag 列表（新增 24.03-lts-sp3、25.09 等条目，调整 latest 指向）。没有新增或移动任何文件，也没有修改任何 Dockerfile、meta.yml、image-list.yml 等与镜像构建直接相关的文件。CI 失败发生在 appstore 发布规范预检阶段，该阶段本应仅校验镜像目录内的文件，不应将仓库根目录的文档类 README 纳入校验范围。因此该失败与 PR 的代码变更**无实质关联**，属于 CI 基础设施/工具层面的误报。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑可能错误地将仓库根目录的 `README.md` 纳入 appstore 发布规范检查范围。根目录的 `README.md` 是项目整体说明文档，不属于任何应用镜像的 appstore 发布物，应从校验文件列表中排除。并非本次 PR 需要修复的问题，属于 CI 工具的配置或代码缺陷。

### 方向 2（置信度: 低）
若 CI 工具实际是通过对比 fork 仓库与主仓库的文件差异来校验路径，可能存在路径前缀解析不一致的问题（如 diff 输出中的 `a/README.md` 或 `b/README.md` 未被正确规范化）。这种情况同样属于 CI 工具实现层面问题。

## 需要进一步确认的点
1. CI 工具 `update.py:273` 的路径校验逻辑具体是如何判断"期望路径"的——是静态规则列表匹配，还是基于 diff 输出的动态比较？
2. 触发该 CI Job 的上游 PR 编号为 3194（`PR 3194 [sunshuang1866:fix/2790 -> master]`），而上下文中的 PR 编号为 2790，需确认 PR 编号映射是否正确，是否存在日志串扰。
3. 同一 CI 流水线中，本次 PR 的实际镜像构建 Job（x86-64、aarch64 等架构 Job）是否正常通过？当前日志仅来自 trigger/编排层 Job 的 appstore 预检步骤，需查看下游构建 Job 日志确认镜像构建本身是否成功。

## 修复验证要求
无。本失败属于 CI 基础设施误报，不涉及对 Dockerfile、源码、正则表达式或外部文件的任何修改。

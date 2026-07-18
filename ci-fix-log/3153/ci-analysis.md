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
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）在扫描 PR 变更文件时，将仓库根目录下的 `README.md` 识别为需要校验的镜像相关文件，检查其路径格式时发现 `README.md`（相对路径）与期望格式 `/README.md`（带前导 `/` 的绝对路径）不匹配，判定为 `FAILURE`。

### 与 PR 变更的关联
**无实质性关联**。PR #3153 仅修改了 `README.md` 和 `README.en.md` 两个纯文档文件（更新基础镜像可用 Tags 列表），不涉及任何 Dockerfile、meta.yml、image-info.yml 等镜像构建文件。CI 的 appstore 预检工具错误地将文档文件纳入了镜像发布规范的校验范围，导致不必要的失败。PR 的改动内容本身是正确且无害的。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具需跳过纯文档变更**。`eulerpublisher` 的 `update.py` 应在检测变更文件差异后、执行 appstore 规范校验前，过滤掉仓库根目录的 `.md` 文档文件（`README.md`、`README.en.md` 等），仅对实际镜像目录下的文件执行路径和规范检查。此修复在 CI 工具侧（`eulerpublisher`），不在本次 PR 范围内。

### 方向 2（置信度: 低）
**CI 路径规范化**。如果 CI 工具预期对所有文件进行校验，则需修正路径表示方式：确保 `update.py:356` 处检测到的差异文件路径统一使用带前导 `/` 的绝对路径格式（从 repo root 起算），与 `update.py:273` 处的校验逻辑保持一致。

## 需要进一步确认的点
- 该 CI job（`multiarch/openeuler/x86-64/openeuler-docker-images`）在触发后对差异文件的路径表示方式：是使用 Git 相对路径还是绝对路径。需确认 `update.py:356` 输出的 `"README.md"`（无前导 `/`）是其原始格式还是日志输出省略了 `/`。
- PR #3184（日志中实际触发的 PR，分支 `sunshuang1866:fix/3153`）与本 PR #3153 的关系——CI 日志是否确实来自 PR #3153 的同一次运行，需要确认以避免错配分析。
- 确认 `eulerpublisher` 中 appstore 预检的预期行为：是否应仅对 `image-list.yml` 中列出的镜像目录内的文件进行校验，而非对仓库中所有变更文件进行全量校验。

## 修复验证要求
（无——本次失败属 CI 基础设施工具误判，不涉及代码或正则 patch 的修改。）

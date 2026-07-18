# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发CI校验
- 新模式症状关键词: The expected path should be, Path Error, appstore, releasing, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检阶段）
- 失败原因: CI 的 appstore 发布规范校验工具对所有 PR 执行路径检查，将变更文件 `README.md` 与 appstore 镜像发布路径规则进行匹配。`README.md` 位于仓库根目录，不匹配任何已有的镜像目录路径模式（如 `{场景}/{镜像名}/{版本}/{os版本}/Dockerfile`），因此被判定为路径错误。本 PR 仅修改根目录下的 `README.md` 和 `README.en.md` 两个文档文件，不涉及任何镜像发布，该 CI 校验本不应适用于此类 PR。

### 与 PR 变更的关联
PR #2790 的变更仅涉及根目录下的两个文件：
- `README.en.md`：更新基础镜像 Tags 列表，新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目，将 "latest" 标签从 sp2 更新为 sp3
- `README.md`：同上（中文版）

这些变更是纯文档维护，不涉及任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 等与镜像构建相关的文件。CI 流水线中的 `eulerpublisher` appstore 校验步骤不应被此类仅文档变更的 PR 触发，但当前流水线未对 PR 变更文件类型做区分，导致误报。

## 修复方向

### 方向 1（置信度: 高）
CI 流水线误报，**Code Fixer 无需处理本 PR 的代码**。这是 CI 基础设施侧的问题——appstore 发布规范检查应对 PR 变更文件做前置过滤：如果变更文件仅包含根目录下的 `README.md`、`README.en.md` 等非镜像相关的文档文件，应跳过 check 步骤。建议将此问题反馈给 CI 流水线维护方，在 `update.py` 的 diff 检测逻辑中增加文件白名单或路径过滤。

### 方向 2（置信度: 中）
若 CI 维护方暂不修复流水线，则本次 PR 可尝试关闭后重新提交观察（可能是触发型 Job `multiarch/openeuler/trigger/openeuler-docker-images` 在编排时将文档 PR 也调度到了 x86-64 构建 Job）。但由于 CI 日志清晰显示错误发生在同一个 Job 内的 `update.py` 脚本，方向 1 更可能是根本原因。

## 需要进一步确认的点
1. CI 流水线配置中，`update.py` 的 appstore spec check 是否对所有 PR 无条件执行，还是基于触发条件（如 `image-list.yml`、`meta.yml` 变更）有条件执行
2. PR #2790 是否是通过 merge_request 触发而并非手动触发，触发日志显示 `PR 3194 [sunshuang1866:fix/2790 -> master] trigger by merge_request`，其中 PR 编号 3194 与 PR #2790 不一致，需确认是否为 Git 平台（如 Gitee/GitLab）生成的临时合并 PR 编号

## 修复验证要求
无——本 PR 为 docs-only PR，不需要任何修复验证。

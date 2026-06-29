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
2026-06-29 15:21:41,552-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（`update.py`）对 PR 变更文件执行路径校验，PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，这两个文件不在 appstore 应用镜像所要求的 `{Category}/{AppName}/...` 子目录路径结构中，因此校验不通过。

### 与 PR 变更的关联
PR 变更仅涉及根目录下 README 文档的 tag 列表更新（新增 24.03-lts-sp3、25.09 等标签条目），属于纯文档维护，**不涉及任何应用镜像 Dockerfile 的新增或修改**。CI 流水线对所有 PR（包括纯文档 PR）均执行了 appstore 发布规范预检，该预检要求变更文件必须符合应用镜像的目录结构规范，导致本次文档 PR 被误报为失败。

## 修复方向

### 方向 1（置信度: 高）
此 PR 为纯文档更新，不应触发 appstore 发布规范校验。检查 CI 流水线的触发条件或校验逻辑，对仅包含根目录文档变更（如 `README.md`、`README.en.md`）的 PR 跳过 appstore 发布规范预检步骤，避免误报。

### 方向 2（置信度: 中）
若 CI 流水线无法按文件类型过滤校验，可考虑在 appstore 校验工具 `update.py` 中增加白名单逻辑：当 PR 变更文件仅限于根目录文档文件时，直接返回校验通过，不执行路径结构检查。

## 需要进一步确认的点
- 确认 CI 流水线（`multiarch/openeuler/trigger/openeuler-docker-images`）的触发条件中是否有区分"应用镜像 PR"和"文档 PR"的逻辑，当前是否对所有 PR 无差别执行 appstore 校验
- 确认 `update.py` 中的路径校验规则是否可以针对非应用镜像目录的文件做豁免处理

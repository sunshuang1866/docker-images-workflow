# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
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
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher`）对所有 PR 中变更的文件执行路径校验，要求变更文件位于 `{category}/{image}/{version}/{os-version}/` 镜像目录结构下。本次 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，这些文件不属于任何镜像目录，触发路径校验失败。

### 与 PR 变更的关联
PR 仅对根目录的 `README.md` 和 `README.en.md` 中的"可用镜像的 Tags"表格做了文档更新（新增 24.03-lts-sp3、25.09 等 Tag 条目并修正链接），没有涉及任何镜像 Dockerfile 或元数据文件的变更。CI 的 appstore 预检未将纯文档类 PR 排除在外，导致误报。**这次 PR 的改动是合法的文档更新，CI 失败与代码质量无关。**

## 修复方向

### 方向 1（置信度: 高）
CI 流水线（`eulerpublisher/update/container/app/update.py`）的预检逻辑需要增加对纯文档类 PR 的豁免：当 PR 中变更的文件仅包含根目录 `README.md`、`README.en.md`、`.github/` 下文件等非镜像目录文件时，应跳过 appstore 路径规范校验，直接通过。这需要修改 CI pipeline 脚本（非本仓库代码），Code Fixer 无需处理本仓库的任何文件。

### 方向 2（置信度: 低）
如果 CI pipeline 脚本不允许直接跳过，也可以考虑在 PR 中追加一个无实际影响的 dummy 文件变更（不推荐），或等待 CI 流水线团队修复该问题后重新触发。但这不是本仓库层面的修复。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中是否有针对根目录文档文件的豁免逻辑（如 exclude 列表），如果有，检查为何未生效。
- 确认该 CI 流水线由哪个团队维护，将预检误报问题反馈给流水线团队进行调整。

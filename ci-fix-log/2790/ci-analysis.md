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
2026-07-14 15:27:59,455-...-INFO: Difference: [
    "README.md"
]
...
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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具检测到 PR 变更了根层级 `README.md`，该文件路径不属于任何已识别的应用镜像发布路径（如 `AI/`、`Bigdata/`、`Database/` 等），不符合 appstore 镜像发布规范，因此路径校验失败。

### 与 PR 变更的关联
PR #2790 仅修改了两个文件：`README.md` 和 `README.en.md`（更新了 openEuler 基础镜像的 Tags 列表，新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目）。CI 的 appstore 发布规范预检（`update.py`）扫描到 `README.md` 存在变更，但该文件位于仓库根目录而非任何应用镜像的子目录中，不满足 appstore 上架规范要求的路径结构（通常为 `{category}/{app-name}/{version}/{os-version}/Dockerfile` 等形式），导致校验失败。

**该失败与 PR 的 README 变更直接相关，但并非 PR 内容有错误**——这是一个纯文档更新 PR，不应触发面向应用镜像发布的 appstore 规范预检。

## 修复方向

### 方向 1（置信度: 高）
该 PR 是纯文档更新（仅修改 README.md / README.en.md），不涉及任何应用镜像的 Dockerfile 变更。此类 PR 不应被 appstore 发布规范预检 CI 流水线处理。建议通过以下方式之一解决：
- CI 流水线层面增加文件白名单过滤：当 PR 变更文件仅为仓库根目录的 `README.md`、`README.en.md` 等文档文件时，跳过 appstore 规范预检步骤。
- 或者在项目 CI 编排中为此类文档更新 PR 使用不包含 appstore 检查的独立流水线。

### 方向 2（置信度: 中）
如果该 PR 确实应触发 appstore 检查，则意味着 CI 对根层级 README.md 路径的判断规则需要更新——当前规则将所有非应用镜像路径的变更视为"路径错误"，但 `/README.md` 是仓库合法文件，其变更不应被视为错误。需要在 `update.py` 的路径校验逻辑中将 `/README.md`（以及 `/README.en.md`）加入豁免列表。

## 需要进一步确认的点
- 此 PR 是否由 `merge_request` 事件触发了错误的工作流（appstore 规范检查而非通用 CI），需确认 CI 编排层中的 trigger 条件配置。
- `update.py:273` 的具体路径校验逻辑：需确认该脚本是否对仓库根目录文件有特殊处理，以及"expected path should be /README.md"错误消息的确切语义（是期望路径为 `/README.md` 但实际不匹配，还是 `/README.md` 不在允许的 appstore 路径白名单中）。

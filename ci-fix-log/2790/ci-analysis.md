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
2026-06-30 11:28:09,089-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 (`update.py`) 对 PR 中变更的文件进行路径校验。PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），这两个文件不属于 appstore 应用镜像的目录结构（如 `{category}/{image}/{version}/{os-version}/Dockerfile`），因此被标注为路径错误，触发 `FAILURE`。

### 与 PR 变更的关联
- **直接相关**：PR 的变更就是这两个 README 文件，CI 的 appstore 规范检查正是针对这些变更文件触发的。
- PR 改动内容（更新 Supported Tags 表格中的版本链接和新增条目）本身无语法错误或格式问题，错误完全来自 CI 路径校验规则与文件所在位置的冲突。
- 该 PR 是根级文档维护（README 中的镜像标签链接更新），本不应触发 appstore 发布规范检查，但 CI pipeline 未区分文档类 PR 与镜像发布类 PR，统一执行了 appstore 校验。

## 修复方向

### 方向 1（置信度: 高）
CI pipeline 的触发条件或 appstore 规范检查应在执行前过滤掉仅涉及根级文档文件（如 `README.md`、`README.en.md`、`LICENSE` 等）的 PR，使纯文档更新的 PR 跳过 appstore 路径校验步骤。这属于 CI 配置层面的调整，而非代码修复。

### 方向 2（置信度: 中）
如果 CI 架构无法区分 PR 类型，可在规范检查工具 `update.py` 中添加白名单机制，对根级文档文件（`/README.md`、`/README.en.md` 等）直接放行，不纳入 appstore 发布路径校验范围。

## 需要进一步确认的点
- CI pipeline 的触发配置：当前是否所有 PR（无论内容）都通过同一个 pipeline 并执行 appstore 规范检查，还是需要由 PR 作者标记或分支命名规则来区分。
- `update.py` 中路径校验逻辑的具体实现：确认白名单/排除规则的修改位置和方式。
- 是否存在其他类似的历史案例（根级文件触发 appstore 路径检查被拒），以确认该问题是偶发还是系统性缺陷。

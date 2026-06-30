# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11 — YAML / 元数据文件错误（appstore 路径校验子模式）
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

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
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具对 PR 中所有变更文件执行路径校验，仓库根目录的 `README.md` 和 `README.en.md` 不符合 appstore 镜像发布规范要求的目录结构（变更文件应位于 `{场景目录}/{镜像名}/{版本号}/{OS版本}/Dockerfile` 等镜像路径下），因此被标记为 `[Path Error]`。

### 与 PR 变更的关联
PR #2790 仅修改了两个文件：
- `README.md` — 更新"可用镜像的Tags"表格，将 latest 标签从 `24.03-lts-sp2` 调整为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目
- `README.en.md` — 同上，英文版同步更新

PR 中没有任何镜像构建相关文件（Dockerfile、meta.yml、image-info.yml 等）的变更，也不涉及任何应用镜像的发布操作。CI appstore 校验器对所有 diff 文件一视同仁地执行路径合规检查，导致纯文档类变更也被拦截。

## 修复方向

### 方向 1（置信度: 高）
这是一个纯文档类 PR，不涉及任何镜像发布操作。CI appstore 路径校验不应阻塞仓库根目录 README 文件的更新。需要确认 CI 校验工具 `update.py` 是否存在白名单机制或跳过逻辑以允许根级文档变更。若确认 README.md / README.en.md 变更属于正常仓库维护操作，应在 CI 校验工具中排除仓库根目录下的 `README.md` 和 `README.en.md` 文件。

### 方向 2（置信度: 中）
如果 CI 校验工具无法修改，可考虑将此类纯文档 PR 通过分支命名约定（如 `docs/*`）或其他机制绕过 appstore 校验阶段。但这依赖于 CI pipeline 的触发/跳过策略配置。

## 需要进一步确认的点
1. CI 校验工具 `eulerpublisher/update/container/app/update.py` 中是否有文件路径白名单或过滤逻辑，是否需要为该工具新增对根级文档文件的豁免。
2. 该 CI pipeline 是否对特定分支模式（如 `docs/*`）跳过 appstore 校验步骤。
3. 确认 PR #2790 的意图是否为纯粹的文档更新——从 diff 来看确是纯文档变更，但需确认是否有其他未体现在 diff 中的关联操作。

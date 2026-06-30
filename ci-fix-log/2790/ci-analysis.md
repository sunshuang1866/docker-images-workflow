# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误，CI appstore 路径校验误报）
- 新模式标题: (留空 — 已有历史模式匹配)
- 新模式症状关键词: (留空 — 已有历史模式匹配)

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对被修改的仓库根目录文档文件 `README.md` 和 `README.en.md` 执行了路径校验。这些文件位于仓库根目录，不在任何镜像类别子目录（`Bigdata/`、`AI/` 等）下，且不属于镜像发布元数据文件（如 `Dockerfile`、`meta.yml`、`image-info.yml`），因此校验工具将其标记为 `[Path Error]`，触发 CI 失败。

### 与 PR 变更的关联
- **PR 仅在两个 README 文件中更新了"可用镜像的 Tags"表格**：将 `24.03-lts-sp2` 改为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目的链接。不涉及任何 Dockerfile、元数据文件或镜像构建相关文件。
- PR 变更内容本身无错误，CI 失败是 appstore 校验工具对纯文档类 PR 的误报——该工具不应在有变化文件均为仓库根级非镜像文件时判定失败。

## 修复方向

### 方向 1（置信度: 中）
**CI 侧豁免纯文档 PR 的 appstore 校验**：在 CI 的 `update.py`（或上游 trigger job）中增加前置过滤逻辑——当 PR diff 中变更的文件**全部**位于仓库根目录（非镜像分类子目录）且不包含 `Dockerfile`、`meta.yml`、`image-info.yml`、`image-list.yml` 时，跳过 appstore 发布规范检查，直接返回成功。

### 方向 2（置信度: 低 — 证据不足）
**修复 update.py 的路径校验逻辑**：如果 `update.py` 内存在一个路径合法性白名单/校验函数，可能缺少对仓库根级 README 文件的豁免规则。但这需要查看 `update.py:273` 附近的具体校验逻辑才能确认。

## 需要进一步确认的点
1. **`update.py:273` 的具体校验逻辑**：需要阅读 `eulerpublisher/update/container/app/update.py` 第 273 行附近代码，确认 `[Path Error]` 的判断条件和期望路径 `/README.md` 的含义（是否指根目录 README 应被豁免，还是校验逻辑本身有缺陷）。
2. **是否有用于记录 PR 级别的 appstore 检查豁免白名单**：确认触发层 job 或 `update.py` 是否已有机制允许某些 PR（如仅修改根级文档）绕过 appstore 校验。
3. **该 job 是否同时作用于多个 PR 上下文**：日志显示 `PR 2809 [sunshuang1866:fix/2790 -> master]`——PR 2809 可能是将 fix/2790 分支合入 master 的合并请求，需确认实际触发 CI 的代码分支与 PR #2790 的 diff 是否一致。

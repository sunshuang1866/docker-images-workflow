# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 被检文件: 仓库根目录 `/README.md`
- 失败原因: CI 的 appstore 发布规范校验工具检测到 PR 变更了根目录 `README.md`，并对其执行 appstore 镜像发布规范检查。由于该文件是仓库文档/索引文件（包含所有镜像 Tags 的目录列表），而非某个具体应用镜像的发布定义文件（不包含 Dockerfile、meta.yml、image-info.yml 等结构），校验工具判断该文件不符合 appstore 镜像发布规范，报 `[Path Error]`。

### 与 PR 变更的关联
**直接关联。** PR #2790 仅修改了两个文件：
- `README.md`（中文根 README）
- `README.en.md`（英文根 README）

变更内容为更新基础镜像 Tags 列表（新增 25.09 条目，将 latest 从 24.03-lts-sp2 更新为 24.03-lts-sp3，补全 24.03-lts-sp2 的独立行）。CI 的 appstore 校验 pipeline（`eulerpublisher/update/container/app/update.py`）扫描了 PR 变更文件列表，对 `README.md` 执行 appstore 发布规范校验。由于根 README.md 本质上不是应用镜像发布文件，触发了校验失败。同类问题在历史模式 11 中有先例（PR #2512: `.claude/agents/README.md` 因路径不符合 appstore 发布规范导致 CI 失败）。

## 修复方向

### 方向 1（置信度: 中）
该 CI 失败是校验工具对根级文档文件过度检查导致的误报。根 `README.md` 和 `README.en.md` 是仓库的文档索引，不应被 appstore 镜像发布规范校验。修复方向：
- 在 CI 校验工具（`eulerpublisher/update/container/app/update.py`）中增加对仓库根目录纯文档文件（无对应 Dockerfile/meta.yml 的 README）的跳过逻辑。
- 或者在 PR 中检查是否存在实际的应用镜像变更（如 Dockerfile、meta.yml 等），若无则跳过 appstore 规范检查。

### 方向 2（置信度: 低）
若校验工具对 README.md 的格式有特定要求（如要求包含特定元数据格式头），可考虑让根 README.md 也包含 appstore 要求的元数据段。但根 README.md 本质是面向用户的文档索引，不应强制套用镜像发布规范格式，此方向合理性存疑。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 的具体校验逻辑——该工具是如何判定 `[Path Error]` 的？是对所有变更文件无差别执行 appstore 规范检查，还是有文件类型过滤逻辑？
2. 根 `README.md` / `README.en.md` 是否应该在 appstore 校验的白名单/排除列表中？这与仓库的 CI 设计意图有关。
3. PR 是否本意仅为文档更新（不涉及任何镜像发布），还是同时预期触发 appstore 发布流程？若是纯文档更新，CI 配置可能需要支持跳过 appstore 检查。

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（近似匹配）
- 新模式标题: 根目录README误触发appstore校验
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, specification errors

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
There are some specification errors for releasing on appstore in this PR, please check as above.

+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具的 appstore 发布规范预检步骤）
- 失败原因: CI appstore 发布规范检查工具（`eulerpublisher`）对仓库根目录下被修改的 `README.md` 执行路径校验，输出 `[Path Error] The expected path should be /README.md` 并标记为 FAILURE。文件实际路径正是 `/README.md`，与错误描述中"期望路径"一致，但校验仍判定失败，说明 CI 检查工具存在对纯文档类 PR（不涉及任何 Docker 镜像构建文件）的处理缺陷——工具可能期望 README.md 出现在特定镜像目录层级（如 `{category}/{image}/{version}/{os-version}/README.md`）而非仓库根目录，或路径校验逻辑存在反直觉的判定规则。

### 与 PR 变更的关联
PR #3153 的 diff 仅包含两个文件：
- `README.md`（仓库根目录）：更新基础镜像可用 tag 列表，将 `24.03-lts-sp2` 修正为 `24.03-lts-sp4`，新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目
- `README.en.md`（仓库根目录）：同上（英文版）

**此 PR 未修改任何 Dockerfile、image-list.yml、meta.yml、image-info.yml 或任何镜像构建相关文件。** 这是一次纯粹的文档更新，不应触发 appstore 镜像发布规范校验。CI 失败是因为 appstore 校验工具对所有包含文件变更的 PR 执行路径检查，且对根目录 README.md 的处理逻辑存在缺陷，导致合法文档变更被误判为路径错误。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 规范检查工具 `eulerpublisher/update/container/app/update.py` 应增加对 PR 变更文件类型的预过滤：当变更文件仅包含仓库根目录下的纯文档文件（如 `README.md`、`README.en.md`）而不涉及任何镜像目录下的 Dockerfile 或元数据文件时，应跳过 appstore 发布规范校验。此为 CI 工具侧修复，非 PR 作者可处理。

### 方向 2（置信度: 低）
若 CI 工具的路径校验逻辑确实期望 README.md 位于某个特定路径模式下（如必须位于镜像目录内），则需要确认 appstore 发布规范中关于仓库根目录 README.md 修改的正式规定。如果规范明确允许根目录 README.md 的独立修改，则应在 CI 工具中将其加入白名单。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 中路径校验逻辑的具体实现——为何文件路径 `/README.md` 与期望路径 `/README.md` 一致时仍判定 FAILURE
2. CI appstore 发布规范是否明确要求所有文件变更必须属于某个镜像的子目录，或是否允许仓库根目录文档的独立 PR
3. 同类纯文档 PR 是否也曾触发相同的 CI 失败（可查询历史 CI 运行记录确认是否为已知问题）

## 修复验证要求
本报告判定失败原因为 CI 基础设施问题（工具对纯文档 PR 的误判），非 PR 代码缺陷。若后续认定为代码侧问题，需先从 CI 工具源码理解路径校验的判定逻辑后再制定修复方案。

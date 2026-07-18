# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根文档路径校验误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, eulerpublisher, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验逻辑）
- 失败原因: CI 流水线中的 appstore 发布规范校验工具（Eulerpublisher `update.py`）对 PR 变更的所有文件进行路径合规性检查。本 PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`（项目文档，非 appstore 镜像入口 README），但校验工具仍将其纳入 appstore 镜像路径校验范围，因根目录路径不符合 appstore 镜像 README 的预期路径规范而报 `Path Error`。

### 与 PR 变更的关联
**与 PR 变更无关**。本 PR 仅更新根目录 README 中可用基础镜像 tag 列表（新增 `24.03-lts-sp4`/`sp3`/`sp2`、`25.09`，修正原有 `sp2`→`sp4` 及 URL 从 SP1→SP4），属于纯粹的文档更新，不涉及任何 appstore 镜像文件的增删改。CI 失败源于校验工具未排除根级项目文档目录，将其错误纳入 appstore 发布路径校验范围。

## 修复方向

### 方向 1（置信度: 中）
CI 侧修改 Eulerpublisher `update.py` 的路径过滤逻辑，在校验 appstore 发布规范前增加前置过滤：仅对位于已知镜像分类子目录（`AI/`、`Bigdata/`、`Cloud/`、`Database/`、`Distroless/`、`HPC/`、`Others/`、`Storage/`）下的文件执行 appstore 路径合规校验，排除根目录项目文档。

### 方向 2（置信度: 低）
在 PR 中添加或修改某个 CI 配置/标签文件，显式声明本次 PR 为纯文档更新，使 CI 跳过 appstore 发布规范校验。此方向需要确认 CI 框架是否支持此类跳过机制。

## 需要进一步确认的点
1. Eulerpublisher `update.py` 中 appstore 校验的入口逻辑和路径白名单/黑名单机制具体实现。
2. 该 CI 校验失败是否属于已知问题（其他纯文档 PR 是否也遭遇同类误报）。
3. 日志中 upstream job 编号为 "build number 2839, PR 3184" 但上下文标记为 PR #3153，需确认日志与 PR 的对应关系是否正确。
4. aarch64 下游 job 是否也触发了相同的校验并失败（日志仅提供了 x86-64 job 的输出）。

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI误触发appstore校验
- 新模式症状关键词: Path Error, expected path, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验管道（`update.py`）检测到 PR 变更了 `README.md`，并对其执行了 appstore 路径校验。根目录的 `README.md` 不是任何应用镜像的文件，不在 appstore 镜像路径结构（如 `{image}/{version}/{os_version}/`）内，因此路径校验失败。

### 与 PR 变更的关联
PR 仅修改了两个根目录级别的文档文件（`README.md` 和 `README.en.md`），将基础镜像可用标签列表更新为最新的发行版（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，调整 24.03-lts-sp2 的链接指向正确的 SP2 目录）。这些是纯文档维护变更，不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-info.yml。CI 的 appstore 校验管道不应被此类变更触发——该管道仅应在 PR 包含应用镜像目录下文件的新增或修改时才执行路径规范检查。

## 修复方向

### 方向 1（置信度: 中）
CI 侧的 `update.py` 在校验变更文件时，应将检查范围限定在应用镜像目录（`Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/`）内，排除根目录级别的文档文件。若 PR 的所有变更文件均不落在上述目录内，应跳过 appstore 规范校验。

### 方向 2（置信度: 低）
若 CI 行为无法变更，则 PR 可能需要满足某种 README 路径结构要求（如 README.md 包含特定的 appstore 元数据头），但这不符合纯文档 PR 的预期——不推荐此方向。

## 需要进一步确认的点
1. CI 日志中显示上游触发的 PR 编号为 3184（`PR 3184 [sunshuang1866:fix/3153 -> master]`），与上下文给定的 PR #3153 不一致。需确认这是否是同一个 CI 运行的日志，或是否存在 PR 编号重映射/关联问题。
2. 需查阅 `update.py` 中 `line:273` 附近的逻辑，确认 appstore 路径校验是否对变更文件做了目录层级过滤，还是对所有变更文件一视同仁。
3. 确认该仓库的 CI 流水线设计意图：根目录 README 的纯文档变更是否预期会触发 appstore 校验管道。若不会，则为 CI 工具 bug；若会，则需明确此类 PR 的合规要求。

## 修复验证要求
不适用——本失败为 infra-error，与 PR 代码变更无关，不涉及 Dockerfile 或正则 patch 修复。

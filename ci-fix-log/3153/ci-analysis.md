# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 校验脚本）
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）对 PR 中变更的 `README.md`（仓库根目录级别）执行了路径校验。该校验将变更文件列表中的路径 `README.md`（无前导 `/`）与期望路径 `/README.md`（带前导 `/`）进行比较，因路径格式不一致（缺少/多余前导斜杠归一化）导致 FAILURE。此 PR 仅修改了仓库根目录的两个 README 文档文件（更新基础镜像可用 Tags 列表），不涉及任何 Dockerfile、meta.yml、image-info.yml 等 appstore 镜像发布文件。CI 校验工具对非 appstore 文件的路径校验逻辑存在缺陷。

### 与 PR 变更的关联
PR 变更内容为纯文档更新：在 `README.md` 和 `README.en.md` 中将基础镜像 Tags 列表从原先的 `24.03-lts-sp2` 更新为最新的 `24.03-lts-sp4`，并补充了 `24.03-lts-sp3`、`25.09` 等中间版本的 Tag 条目。这些改动不涉及任何构建逻辑、Dockerfile、依赖或镜像元数据。

CI 失败与 PR 代码变更无直接关联——失败原因是 CI 自身的 appstore 路径校验脚本对仓库根目录 README.md 的路径比较逻辑存在缺陷（路径格式归一化问题），而非 PR 引入的错误。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `eulerpublisher/update/container/app/update.py` 中路径比较缺少前导 `/` 归一化处理。在比较变更文件路径与期望路径时，应对两侧路径统一进行 `os.path.normpath` 或添加前导 `/` 标准化处理（如 `os.path.join('/', path)`），确保 `README.md` 和 `/README.md` 在同一次比较中被视为等价。

### 方向 2（置信度: 低）
若 CI 校验工具的设计意图是仅校验 appstore 镜像发布相关目录下的文件，则应在路径校验前增加过滤条件：仅对属于 appstore 镜像目录（如 `AI/`、`Bigdata/`、`Database/` 等子目录）下的文件执行路径规范校验，跳过仓库根目录的文档文件。根目录 `README.md` 属于仓库级文档，不应纳入 appstore 发布规范的校验范围。

## 需要进一步确认的点
- CI 校验工具 `eulerpublisher/update/container/app/update.py` 中路径比较的具体实现逻辑（第 273 行附近的路径校验代码），以确认是前导 `/` 归一化缺失还是其他路径构建问题。
- 该 CI 校验原本的预期行为：是仅校验 appstore 镜像目录内的文件，还是校验仓库中所有变更文件。如为后者，需确认根目录 README.md 在 appstore 发布规范中的定位和预期路径格式。

## 修复验证要求
code-fixer 必须：
1. 从 eulerpublisher 仓库对应版本的 `eulerpublisher/update/container/app/update.py` 获取第 273 行附近的路径校验逻辑，确认路径比较的实际实现方式。
2. 验证修复后，仓库根目录 README.md 的路径 `README.md` 能被正确识别为 `/README.md`（或反之），确保 Path Error 不再触发。

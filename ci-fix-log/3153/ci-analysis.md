# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误）— 部分匹配，CI appstore 路径校验失败
- 新模式标题: 根目录文档路径校验误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,043-INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 规范校验阶段）
- 失败原因: CI appstore 发布规范预检脚本 (`update.py`) 检测到 PR 变更了仓库根目录的 `README.md` 文件，该校验将根目录文档标记为路径不符合 appstore 发布规范，导致检查失败。该检查本应用于应用镜像目录（如 `Bigdata/`、`AI/` 等）内的文件路径校验，但被错误地应用于仓库根目录的纯文档变更。

### 与 PR 变更的关联
PR 仅修改了两个文件：
- `README.md` — 更新基础镜像可用 Tag 列表（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09` 条目，修正 `24.03-lts-sp2` 的 URL）
- `README.en.md` — 同步更新英文版的 Tag 列表

PR 的改动**不涉及任何应用镜像的 Dockerfile、meta.yml、image-info.yml 等构建相关文件**，是一个纯文档更新。CI 失败由 appstore 规范校验脚本误将根目录 `README.md` 纳入应用镜像路径检查范围导致，**与 PR 内容正确性无关**。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 规范校验脚本 `update.py` 在检测 PR 变更文件时未区分仓库根目录文档与应用镜像目录文件。需要在 `update.py:273` 附近的路径校验逻辑中添加过滤，跳过仓库根目录的 `README.md`、`README.en.md` 等非应用镜像目录内的文件变更，避免对纯文档 PR 产生误报。

### 方向 2（置信度: 低）
PR 中的 README.md 变更内容本身可能不符合 appstore 发布规范的某种格式要求（如 Tag 列表格式、链接格式等），导致 CI 将其标记为失败。但从错误信息看，明确显示的是 `[Path Error]`（路径错误）而非内容格式错误，方向 1 的可能性更高。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的具体校验逻辑——需要阅读源码确认路径检查的完整条件分支，判断为什么根目录 `/README.md` 会被标记为 `[Path Error]`。
2. CI 对纯文档 PR（如 README 更新）是否有跳过 appstore 预检的机制——若有，该机制为何未生效；若无，是否应将其作为 CI 流程改进项。
3. 该 CI 流程是否在所有 PR（含文档 PR）上运行，还是仅在 detect 到特定目录变更时触发——需确认 `Difference` 检测逻辑的触发条件。
4. 日志中 PR 编号为 3184（`PR 3184 [sunshuang1866:fix/3153 -> master] trigger by merge_request`），但上下文 PR 编号为 3153，需确认两者是否指向同一变更或存在日志归属错误。

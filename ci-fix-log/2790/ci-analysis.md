# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (N/A)
- 新模式症状关键词: (N/A)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI appstore 路径校验工具对仓库根目录的 `README.md` 文件执行了路径格式检查，工具以 `/README.md`（带前导斜杠）为期望格式，但 git diff 产出的路径为 `README.md`（无前导斜杠），字符串比较不匹配导致 `[Path Error]`。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的两个文档文件：
- `README.md` — 更新支持的 Tags 列表（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目，修正 24.03-lts-sp2 的 URL 指向）
- `README.en.md` — 同上（英文版）

PR **未修改任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml**，也没有新增或删除任何镜像目录文件。变更属于纯粹的文档维护，不涉及应用镜像的构建逻辑或元数据。

失败的直接原因是 CI appstore 路径校验工具将根目录 `README.md` 纳入了应用镜像路径规范检查（`[Path Error] The expected path should be /README.md`），而根目录 README 文件不属于应用镜像发布路径范畴，不应受该规则约束。日志中 DIFF 检测仅列出了 `README.md`（未列出 `README.en.md`），进一步说明该检查的目标是仓库根级文档文件而非应用镜像文件。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 路径校验工具（`update.py` 第 273 行附近）对修改文件的路径格式校验过于严格或覆盖范围过大：其将 git diff 输出的相对路径（`README.md`）与内部约定的绝对路径格式（`/README.md`）做精确字符串比较，导致根目录文件的路径检查误报。需要在 `update.py` 中将路径比较逻辑改为先统一规范化路径格式（如统一添加/移除前导 `/` 或使用 `os.path.normpath`），再进行比较。

### 方向 2（置信度: 低）
若 CI 工具设计意图是仅对 `Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/` 子目录下的文件执行 appstore 路径校验，则当前工具缺少对仓库根目录文件的跳过逻辑（白名单/过滤）。可在 `update.py` 的 DIFF 检测阶段增加路径前缀过滤，对不在上述场景目录下的文件跳过 appstore 规范检查。

## 需要进一步确认的点
1. 查阅 `eulerpublisher/update/container/app/update.py` 第 220-280 行的具体实现逻辑，确认路径比较时是否进行了规范化处理（前导斜杠统一）。
2. 确认 CI appstore 路径校验的设计预期范围——根目录 `README.md` 是否应该被纳入检查（当前日志表明它被纳入了）。
3. 日志中 DIFF 只检测到 `README.md` 而未检测到 `README.en.md` 的原因（可能 diff 检测逻辑仅关注了 `README.md`，或 `README.en.md` 被过滤）。

## 修复验证要求
(N/A — 不涉及正则 patch 外部源文件)

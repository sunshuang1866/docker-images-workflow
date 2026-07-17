# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（关联 模式11）
- 新模式标题: 根级文档CI误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 变更文件 `README.md`（仓库根目录）执行路径校验，报告 `[Path Error] The expected path should be /README.md`。但 `README.md` 实际上就位于仓库根目录 `/README.md`，与实际预期路径完全一致，此错误为 CI 工具的误报。

### 与 PR 变更的关联
PR 仅修改了两个文档文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 Tag 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，更新 latest 指向）。变更内容本身正确无误。

CI 预检工具检测到 `README.md` 发生变更后，将其纳入 appstore 发布规范校验流程。`README.md` 属于仓库根目录的纯文档文件，并非应用镜像的 Dockerfile 或元数据文件，不应受 appstore 发布规范约束。CI 校验工具对此类根级文档文件缺乏豁免逻辑，导致误报 `Path Error`。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题 — 与 PR 代码变更无关。`eulerpublisher` 工具的 `update.py` 对根目录变更文件（如 `README.md`）的 appstore 规范校验缺少例外处理逻辑。需要 CI 工具侧增加判断：当变更文件为仓库根级文档（非镜像目录下的 Dockerfile/meta.yml/image-list.yml）时，跳过 appstore 路径格式校验。PR 作者无需修改代码，可尝试关闭并重新打开 PR 或触发重试。

### 方向 2（置信度: 低）
PR 的 CI 可能因与另一 PR #3184 的并发触发产生关联。Jenkins 日志显示 `PR 3184 [sunshuang1866:fix/3153 -> master] trigger by merge_request`，而当前 PR 编号为 3153，分支名为 `fix/3153`。Jenkins 内部 PR 编号映射异常（3184 vs 3153）可能导致 CI 拉取了错误的比较基线或分支内容，间接引发路径校验失败。

## 需要进一步确认的点
1. CI 日志中 Jenkins 显示 `PR 3184` 而实际 PR 为 #3153，需确认 Jenkins 的 PR 编号与 GitHub PR 编号的映射关系是否存在异常
2. 需确认 `eulerpublisher/update/container/app/update.py:273` 处对根目录文档文件的处理逻辑，是否存在已知缺陷或配置缺失
3. PR #3184（如果存在）是否属于同一作者 `sunshuang1866`、同一分支 `fix/3153`，是否存在 PR 创建/关闭导致的 CI 串号问题

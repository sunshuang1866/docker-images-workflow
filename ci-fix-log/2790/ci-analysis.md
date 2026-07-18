# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径校验不合规
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-.../update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 预检阶段，`eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根级文档文件 `README.md` 和 `README.en.md`（更新基础镜像 Tags 列表），CI 的 appstore 发布规范预检工具（`eulerpublisher`）在扫描 PR diff 时对 `README.md` 执行路径校验，但该文件位于仓库根目录，不匹配任何镜像目录的路径规范（如 `{image-version}/{os-version}/Dockerfile`），导致路径校验失败。

### 与 PR 变更的关联
PR 的 4 个 diff hunk 均为对 `README.md`/`README.en.md` 中基础镜像 Tags 列表的纯文档更新——将 latest 标记从 `24.03-lts-sp2` 切换到 `24.03-lts-sp3`，并补充了 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 独立条目。PR 不包含任何 Dockerfile、meta.yml、image-info.yml 等应用镜像文件变更。CI 预检工具对根级文档执行了镜像发布路径校验，校验本身与 PR 的实际改动性质不匹配，导致误报失败。

## 修复方向

### 方向 1（置信度: 中）
PR 仅涉及根级文档变更，不涉及任何应用镜像 Dockerfile 或元数据文件。此类纯文档变更不应触发 appstore 发布规范的路径校验。需要确认 CI 预检工具的逻辑——是否应跳过仓库根级非镜像文件的路径检查，或将根级 README.md 加入白名单豁免校验。

### 方向 2（置信度: 低）
PR diff 中 `README.md` 的 git 格式路径为 `a/README.md`（带 `a/` 前缀），CI 工具可能未正确处理 git diff 路径前缀，期望的是 `/README.md`（绝对路径）。若这属于 CI 工具的路径规范化 bug，则属于 infra-error，与 PR 变更无关。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现——校验规则是否只适用于 `{category}/{image}/{version}/{os-version}/` 结构下的文件，对根级文件应如何处理。
2. 同类仓库的同类 PR（仅修改根 README）历史上是否能通过 CI 检查，以判断这是否为近期 CI 工具行为变更所致。
3. 确认 `README.en.md` 是否也在校验中被检查——日志中 `Difference` 只列出了 `README.md`，但 PR 同时修改了两个文件。

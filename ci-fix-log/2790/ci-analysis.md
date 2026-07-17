# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR触发校验误报
- 新模式症状关键词: Path Error, expected path, README.md, specification error, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具 `eulerpublisher`）
- 失败原因: CI 的 appstore 发布规范预检工具（`eulerpublisher` 的 `update.py`）对 PR 中变更的根目录 `README.md` 执行了镜像发布规范校验，但根目录 `README.md` 不符合 Docker 镜像文件的目录结构规范（应为 `{category}/{image}/{version}/{os-version}/Dockerfile` 等格式），导致 `[Path Error] The expected path should be /README.md` 校验失败。

### 与 PR 变更的关联
该 PR 仅修改了仓库根目录的两个文档文件（`README.md` 和 `README.en.md`），更新基础镜像可用 Tags 列表（新增 24.03-lts-sp3、25.09、24.03-lts-sp2 条目）。没有任何 Dockerfile、meta.yml、image-info.yml 等镜像构建文件的变更。CI 工具在扫描 diff 时以 `README.md` 为变更文件，并对其执行了仅适用于镜像目录的 appstore 发布规范校验，导致了误报。

## 修复方向

### 方向 1（置信度: 中）
CI 编排工具 `eulerpublisher` 的路径校验逻辑中缺少对根目录文档文件（`README.md`、`README.en.md` 等）的豁免处理。应在 `update.py` 的 diff 文件遍历阶段过滤掉不属于镜像构成文件的变更路径（如仓库根目录的文档文件），避免对这类文件执行 `{image}/{version}/{os-version}` 格式的路径校验。

### 方向 2（置信度: 低）
若该 CI 失败是本应被 CI 编排层（trigger job）正确路由但未路由的情况，实际上 TR 编号 3194 的触发（`sunshuang1866:fix/2790 -> master`）说明这是一个从外部 fork 提交的 PR，CI trigger job 可能未能正确识别该 PR 为纯文档变更并跳过下游架构构建 job。此方向需要更多编排层日志才能确认。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 前后的路径校验逻辑——确认校验函数是否区分"镜像发布文件"与"仓库文档文件"，具体过滤条件是什么。
2. CI 编排层 trigger job（`multiarch/openeuler/trigger/openeuler-docker-images`）是否具备按 diff 类型跳过 appstore 规范校验的机制。
3. 历史 PR 中是否存在其他纯文档变更 PR 在 CI 中通过（或同样失败）的案例，以判断这是已知行为还是近期回归。

## 修复验证要求
若修复涉及修改 `eulerpublisher` 工具的校验逻辑（如在 `update.py` 中增加文件过滤条件），code-fixer 必须在修改后通过以下方式验证：
1. 模拟一个仅包含根目录 README 变更的 PR diff，传入修改后的校验逻辑，确认不再触发 `[Path Error]`。
2. 同时验证正常的镜像 PR（包含 Dockerfile 且目录结构正确）仍能通过路径校验，确保过滤条件不会过度放宽。

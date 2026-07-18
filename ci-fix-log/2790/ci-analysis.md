# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误 — 路径校验子类）
- 新模式标题: 根级文档触发Appstore检查
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检对 PR 中变更的所有文件进行路径校验。PR 仅修改了根级 `README.md`（路径 `/README.md`），该文件不属于任何应用镜像目录（非 `AI/`、`Bigdata/` 等子目录下的文件），appstore 路径校验器将其判定为不符合应用镜像发布规范，报告 `Path Error`。

### 与 PR 变更的关联
此 PR 的 diff 仅包含两个根级 README 文件（`README.md`、`README.en.md`）的标签列表更新——属于纯文档改动。CI appstore 发布规范检查被触发后，对变更文件逐一校验其是否符合应用镜像路径结构（如 `{分类}/{镜像名}/{版本号}/{os-version}/Dockerfile`），根级 `README.md` 不匹配任何应用镜像路径模板，导致路径校验失败。此失败与 PR 改动内容（标签文本）**无关**，与 PR 改动的文件范围（仅根级 README）**直接相关**。

**额外观察**（CI 未报但值得注意）：PR diff 中将 `24.03-lts-sp3` 作为两行添加——一行作为 `[24.03-lts-sp3, 24.03, latest]`，另一行作为 `[24.03-lts-sp3]` 独立条目——存在标签重复，但 CI 当前未对此做内容校验。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线的 appstore 发布规范检查不应拦截纯文档 PR。根本修复需在 `eulerpublisher/update/container/app/update.py` 中增加变更文件过滤逻辑，对根级非映像目录下的文件（如项目根目录的 `README.md`、`README.en.md`）跳过 appstore 路径校验。短期规避方案：PR 中除 README 变更外，可附带一个无关的 app 镜像目录下合法文件的改动（但不推荐）。

### 方向 2（置信度: 低）
PR diff 中 `24.03-lts-sp3` 标签重复（同时作为 `latest` 行和独立行出现），虽非本次 CI 报错原因，但若 appstore 后续增加了内容去重校验，可能引发二次失败。建议合并重复行。

## 需要进一步确认的点
- CI 日志仅捕获了 `README.md` 的路径校验失败，未显示 `README.en.md` 是否也被检查或是否也失败。可能是 CI 只取了 diff 文件列表中的第一个，也可能是 `README.en.md` 通过了检查。需确认 `eulerpublisher/update/container/app/update.py` 中对 diff 文件列表的遍历逻辑是否完整。
- 不确定该 appstore 检查是否为所有 PR 的强制门禁（包括纯文档 PR），还是本次由 merge request 触发条件误配导致。需确认上游 trigger 项目（`multiarch/openeuler/trigger/openeuler-docker-images`）的 pipeline 配置中是否有按文件类型过滤触发条件的机制。
- 需确认 `update.py:273` 处 `[Path Error] The expected path should be /README.md` 的确切含义：是"文件 `README.md` 当前路径 `/README.md` 不符合预期格式"（期望其在应用目录下），还是文字表述有误、实际应报"文件 `/README.md` 不属于任何已知应用镜像路径"。

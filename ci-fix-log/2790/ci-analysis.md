# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: appstore校验误报
- 新模式症状关键词: Path Error, expected path, README.md, appstore, specification error, update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: CI 流水线在 x86-64 下游 job 中运行了 appstore 发布规范校验器（`update.py`），该校验器检测到 PR 变更文件为 `README.md`（及 `README.en.md`），但此 PR 为纯文档更新**不包含任何应用镜像发布内容**（无 Dockerfile、meta.yml 等），校验器将其视为不符合 appstore 发布规范路径的变更，报 `[Path Error]`。

### 与 PR 变更的关联
本次 PR 仅修改了 `README.md` 和 `README.en.md` 两个根目录文档文件，更新了"可用镜像的 Tags"列表（将 latest 标签从 24.03-lts-sp2 改为 24.03-lts-sp3，新增 25.09 条目等）。这些变更**不涉及**任何应用镜像的 Dockerfile、meta.yml、image-info.yml 或 image-list.yml，因此 appstore 发布规范校验与此 PR 无关。CI 流水线错误地将该文档 PR 当作应用镜像发布 PR 进行了校验，导致误报。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线/触发器在调度下游 job 时未区分 PR 的变更类型，将纯文档更新 PR 也送入了 appstore 发布规范校验流程。应在 trigger 层增加文件变更过滤逻辑：当 PR 仅包含根目录 README/文档变更且不包含应用镜像目录变更时，跳过 appstore 规范校验 job。

### 方向 2（置信度: 低）
`eulerpublisher/update/container/app/update.py` 校验器自身对根目录 `README.md` 的路径校验规则可能存在缺陷。「The expected path should be /README.md」提示期望路径与实际路径一致却仍报 FAILURE，可能为校验逻辑 bug。需排查 `update.py:273` 附近的路径比较逻辑是否正确处理了根路径。

## 需要进一步确认的点
1. CI 触发器（`multiarch/openeuler/trigger/openeuler-docker-images`）是否有根据 PR 变更文件类型过滤下游 job 的机制？若无，这是基础设施层面的问题，Code Fixer 无法介入。
2. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的具体路径校验逻辑是什么？需在代码库中查阅 `update.py` 源码确认"Path Error"的判定条件。
3. 根目录 `README.md` / `README.en.md` 的变更在 CI 规范中是否被允许？是否要求必须伴随应用镜像的实质性变更？
4. 上游 trigger job（build number 2783）的日志需确认 — 它是否也以 `Finished: SUCCESS` 结束，仅将失败传播到下游？若是，需获取 trigger 层日志确认其调度逻辑。

## 修复验证要求
若修复方向涉及修改 CI 校验规则（如 `update.py` 中的路径匹配逻辑），Code Fixer 必须在提交前验证：
- 模拟一个仅含 README 变更的 PR 场景，确认修改后的校验器不再误报
- 模拟一个含应用镜像 Dockerfile 变更的 PR 场景，确认修改后校验器仍能正确拦截不合规路径

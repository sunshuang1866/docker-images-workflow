# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发布校验
- 新模式症状关键词: Path Error, expected path should be, appstore specification errors, README.md

## 根因分析

### 直接错误
```
2026-06-29 15:21:41,552-/home/jenkins/agent-working-dir/workspace/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

CI 从 PR diff 中检测到变更文件为 `README.en.md` 和 `README.md`，将其提交至 appstore 发布规范校验器，两条变更均因路径不符合镜像发布规范而失败。

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验器将仓库级（repo root）的 README 文档变更误判为应用镜像发布制品，对其执行路径校验。期望路径应为镜像目录内的相对路径（如 `{category}/{image}/{version}/{os-version}/README.md`），而仓库根目录下的 `README.md` 和 `README.en.md` 不满足该路径约束，校验失败。

### 与 PR 变更的关联
PR 仅修改了两个仓库级的 README 文件（更新支持的 Tags 列表：将 latest 标签从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09` 标签），属于纯文档维护，不涉及任何容器镜像的构建或发布。失败由 CI 流水线错误地将文档 PR 纳入 appstore 发布校验流程导致，与 PR 变更内容是否正确无关。

## 修复方向

### 方向 1（置信度: 中）
CI 流水线（`update.py`）应增加对纯文档 PR 的识别逻辑：当 PR diff 中的变更文件仅包含仓库级 README（`README.md`、`README.en.md`）且不涉及任何镜像目录下的文件时，跳过 appstore 发布规范校验，直接放行。具体地，可在 `update.py` 的 diff 分析阶段增加过滤条件，排除仓库根目录下的非镜像文档文件。

### 方向 2（置信度: 低）
若 CI 流水线的设计意图是将仓库级 README 变更也纳入 appstore 发布校验（例如认为基础镜像 `openeuler/openeuler` 的文档也属于发布范畴），则需要将 `Base/openeuler/` 目录配置为该 PR 所涉 README 的合法路径宿主，并在校验逻辑中建立仓库级 README 到 `Base/openeuler` 目录的映射。

## 需要进一步确认的点
1. CI 校验器 `update.py` 中触发发布校验的条件逻辑是什么——是否为所有触及 README 文件的 PR 均触发，还是仅在 diff 包含特定目录文件时触发。
2. 当前 CI 流水线是否存在已知的机制来区分"镜像发布 PR"与"文档维护 PR"。
3. 确认上游 CI 团队对此类文档 PR 误触发校验问题是否已有解决方案或已知 issue。

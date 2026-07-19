# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 `eulerpublisher` 检测到 PR 变更了仓库根目录的 `README.md`，并对其执行了 appstore 发布路径校验，结果判定为 FAILURE。该 PR 为纯文档更新（仅修改了 README.md 和 README.en.md 中的可用镜像 Tags 列表），不含任何 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 变更，不涉及镜像发布，因此该检查属于误报——CI 对不适用 appstore 发布场景的 PR 错误地执行了发布规范校验。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录下 `README.md` 和 `README.en.md` 中的 Tags 支持列表（更新 24.03-lts-sp2 → 24.03-lts-sp3、新增 25.09 和 24.03-lts-sp2 条目），属于纯文档维护变更。该变更本身不涉及任何镜像的构建、发布或目录结构调整。CI 流水线中的 appstore 发布预检环节未能识别此 PR 为文档专用变更，仍对其执行了镜像发布路径规范校验，导致校验失败。**此失败与 PR 改动内容无关，属于 CI 基础设施对变更类型的误判。**

## 修复方向

### 方向 1（置信度: 中）
CI 流水线在运行 `eulerpublisher` 的 appstore 发布规范检查前，增加对变更文件类型的判断：若 PR 仅包含根目录文档文件（如 `README.md`、`README.en.md`），且无任何镜像目录（`Bigdata/`、`AI/`、`Database/` 等）下的 Dockerfile、meta.yml、image-info.yml 或 image-list.yml 变更，则跳过 appstore 发布校验步骤，直接返回通过。这需要在 CI 编排层（Jenkins job 或 trigger 脚本）实现。

### 方向 2（置信度: 低）
若无法从 CI 编排层面修改校验条件，可考虑将本次 README 更新合并到某个包含实际镜像变更的后续 PR 中一并提交，使 CI 的 appstore 校验对象为该镜像变更而非根目录 README。此方式仅为绕过策略，不解决根本问题。

## 需要进一步确认的点
1. CI 流水线的 trigger/编排层脚本（Jenkins job 配置、shell 调度脚本等）中 `eulerpublisher` appstore 校验的触发条件是什么——是否为所有 PR 全量触发，无法区分文档 PR 与镜像 PR。
2. `update.py:273` 前后的路径校验逻辑具体如何实现：`[Path Error] The expected path should be /README.md` 的错误描述含义不够明确——是期望文件在 `/README.md` 但实际未找到，还是期望文件不在 `/README.md` 而应在其他路径。需查看 `eulerpublisher` 源码中路径校验规则的生成逻辑以确认。
3. 历史上纯文档更新的 PR 是否也有相同失败——若确认为首次出现或已知问题，可确认 CI 流水线本身存在缺陷。

## 修复验证要求
无需对正则或外部源文件进行修复验证。若按方向 1 修改 CI 编排逻辑，需在变更后以纯文档 PR 重新触发 CI，确认 appstore 校验步骤已被跳过且流水线整体通过。

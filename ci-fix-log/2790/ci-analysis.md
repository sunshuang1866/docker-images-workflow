# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档变更误触发AppStore校验
- 新模式症状关键词: README.md, Path Error, appstore, release specification, update.py, eulerpublisher

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
- 失败位置: CI appstore 发布规范校验阶段（`eulerpublisher/update/container/app/update.py:273`）
- 失败原因: CI 的 appstore 发布规范校验流水线对纯文档变更 PR 也执行了路径校验，根目录 `README.md` 不属于任何应用镜像提交目录结构（应位于 `{category}/{app-name}/{version}/{os-version}/` 下），被判定为路径错误。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的两个 README 文件（`README.md` 和 `README.en.md`），更新了基础镜像 Tags 列表（新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，调整了 latest 指向）。这些变更完全不涉及任何应用镜像的新增或修改，CI 的 appstore 发布规范校验不应在此类文档 PR 上阻塞。该失败与 PR 代码质量无关，属于 CI 流水线对 PR 类型判断不足所致的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI 流水线层面增加 PR 类型判定逻辑：当 PR diff 仅包含根目录 README 文件（或更广泛地，不包含任何应用镜像目录 `{category}/{app-name}/{version}/{os-version}/` 下的文件）时，跳过 appstore 发布规范校验步骤。这需要在 `eulerpublisher/update/container/app/update.py` 或 CI 编排脚本中添加文件变更路径的前置过滤。

### 方向 2（可选，置信度: 低）
如果 CI 工具暂不支持跳过校验，可临时在仓库中为根目录 README 文件注册白名单规则，使其被 appstore 校验所接受。但这属于治标方案，建议优先采用方向 1。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑，核实是否有白名单机制可用于排除根目录文档文件。
- 确认 CI 编排脚本（Jenkins pipeline）中是否有条件判断节点，是否可以为纯文档 PR 添加跳过 appstore 校验的分支。
- 确认同类仓库中是否有其他纯文档 PR（如仅修改 README.md）通过 CI 的历史案例，以判断这是本次特例还是系统性问题。

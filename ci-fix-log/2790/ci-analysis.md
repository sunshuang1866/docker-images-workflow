# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-30 11:28:03,983 - INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-30 11:28:09,089 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 变更的文件执行路径校验，根目录下的 `README.md` 和 `README.en.md` 不在任何应用镜像子目录内，不符合 appstore 镜像发布路径规范（期望路径为 `{category}/{image}/{version}/{os-version}/` 层级结构），被标记为 `[Path Error]`。

### 与 PR 变更的关联

本次 PR **仅修改了两个根目录文档文件**（`README.md` 和 `README.en.md` 中的 Supported Tags 列表），未涉及任何应用镜像的 Dockerfile、meta.yml 或 image-list.yml。PR 的文档变更本身是合法且正确的。

CI 失败是因为 appstore 发布规范预检工具对 PR 中**所有变更文件**进行路径校验，包括根目录的项目文档文件。这类文档文件不在任何应用镜像子目录中，天然不满足 appstore 镜像路径规范，导致校验失败。**这是 CI 校验逻辑过度覆盖的问题，而非 PR 改动的错误。**

## 修复方向

### 方向 1（置信度: 中）
在 CI 流水线的 appstore 校验阶段（`update.py` 或上游 trigger 流水线）中，将根目录下的项目文档文件（如 `README.md`、`README.en.md`、`.claude/README.md` 等）加入豁免名单，使其不被纳入 appstore 镜像发布规范的路径校验范围。这类文件属于仓库顶层文档，不应要求其符合应用镜像路径规范。

### 方向 2（置信度: 低）
如果此 CI 流水线仅应在有应用镜像文件变更时触发，则应在上游 trigger 流水线（`multiarch/openeuler/trigger/openeuler-docker-images`）的触发条件中增加判断：若 PR 变更仅为文档类文件（非 Dockerfile、meta.yml、image-info.yml 等），则跳过 x86-64/aarch64 等架构构建流水线的触发。

## 需要进一步确认的点
1. 当前 CI 流水线的触发条件是什么——是否所有 PR 都会触发多架构构建流水线，还是仅包含 Dockerfile 变更的 PR 才会触发？
2. `update.py:273` 的行号与仓库中的实际 `eulerpublisher` 源码是否对应（日志中显示的是 CI 节点上的路径，非仓库内路径），如果仓库中无 eulerpublisher 源码，则修复需在 CI 配置层面进行。
3. 该 appstore 校验是 Jenkins Pipeline 内置逻辑还是通过仓库内的 `eulerpublisher` 脚本执行，这决定了修复位置是 Jenkins job 配置还是仓库脚本。

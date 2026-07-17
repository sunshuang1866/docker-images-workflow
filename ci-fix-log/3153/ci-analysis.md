# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发流水线检查
- 新模式症状关键词: Path Error, The expected path should be, appstore, README.md, docs-only PR

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
...
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR #3153 是一个纯文档更新 PR（仅修改仓库根目录下的 `README.md` 和 `README.en.md`），但 CI 流水线触发了 appstore 发布规范预检。检查器对变更文件 `README.md` 进行路径校验，报 "Path Error" 并声称期望路径为 `/README.md`，而 `README.md` 的实际路径正是仓库根目录 `/README.md`——两者的路径描述一致，不应产生 FAILURE。这表明 CI 路径校验工具在处理根级纯文档变更时存在逻辑缺陷（如误将非镜像目录变更提交至 appstore 检查），属于 CI 基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 仅修改了两个文件：`README.md` 和 `README.en.md`，均为基础镜像可用 tags 列表的文档更新（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，移除旧的一行）。变更内容本身正确、无语法错误，不涉及任何 Dockerfile、meta.yml、image-list.yml 或应用镜像目录的创建/修改。CI 失败与代码变更无因果关系——即使此次变更完全回退，同样的检查器仍可能对任何触及其路径的根级 README 变更报错。

## 修复方向

### 方向 1（置信度: 低）
CI 流水线的 trigger 条件可能过于宽泛，将纯文档 PR 也纳入了 appstore 发布规范检查流程。若流水线配置允许，可增加对变更文件类型的过滤——当 PR 仅修改 `README.md`、`README.en.md`、`.github/` 等非镜像目录文件时，跳过 appstore 发布规范预检，直接进入下游构建或不触发完整 pipeline。

### 方向 2（置信度: 低）
`eulerpublisher/update/container/app/update.py` 的路径校验逻辑可能存在缺陷——对根级文件（如 `README.md`）的路径归一化处理与预期路径比较时产生了不一致。需查阅 `update.py` 源码中路径校验部分的实现，确认是否对非镜像目录变更做了正确的豁免处理。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行前后的路径校验逻辑具体如何实现，为何对根级 `README.md` 产出 "expected path should be /README.md" 的错误。
2. CI pipeline（`multiarch/openeuler/trigger/openeuler-docker-images`）的 trigger 条件配置——纯文档 PR 是否应该触发完整的 appstore 发布规范检查。
3. 分支名 `fix/3153` 中的数字 3153 正好对应 PR 编号，是否存在 PR 描述或分支命名触发了特殊 CI 行为（如被误识别为某类修复任务的流水线触发规则）。

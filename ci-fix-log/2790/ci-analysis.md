# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (无)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（eulerpublisher）将 PR 中变更的仓库根目录 `README.md` 视为 appstore 上架文件进行路径校验，但仓库根目录的 `README.md` 不符合 appstore 镜像条目所要求的 `{category}/{image-name}/{version}/{os-version}/README.md` 层级路径格式，导致路径校验失败。

### 与 PR 变更的关联
PR #2790 仅修改了仓库根目录的两个 README 文件（`README.md` 和 `README.en.md`），更新了基础镜像的 Tags 列表（新增 25.09、24.03-lts-sp3 条目，恢复 24.03-lts-sp2 条目）。CI 工具的 diff 检测识别到 `README.md` 变更后，错误地将其纳入 appstore 发布规范检查流程，触发路径校验失败。PR 的文档更新本身没有错误，失败是由 CI 工具未区分仓库根目录文档与 appstore 镜像目录文档所致。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher/update/container/app/update.py` 中的 diff 文件过滤逻辑未排除仓库根目录的非镜像文件。对于仅变更根目录文档、不涉及任何 `{category}/` 目录下文件的 PR，CI 应直接跳过 appstore 路径校验。修复方式为使 CI 工具仅对位于 `Base/`、`AI/`、`Bigdata/`、`Cloud/`、`Database/`、`Distroless/`、`HPC/`、`Others/`、`Storage/` 等镜像分类目录下的文件执行 appstore 路径校验。

### 方向 2（置信度: 中）
若 CI 工具无法在工具侧修改（可能属于基础设施团队管辖范围），可考虑在仓库根目录添加 CI 忽略配置，使根目录 README.md 不触发 appstore 校验。但这属于绕过方案，推荐方向 1。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 273 行附近的 `update` 函数实现，确认 diff 文件过滤的现有逻辑和可修改点。
- 该 CI 工具代码是否在本仓库中可直接修改，或归属于独立的 eulerpublisher 仓库。

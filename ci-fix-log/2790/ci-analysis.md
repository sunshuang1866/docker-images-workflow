# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-06-30 11:28:09,089-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具 (`update.py`) 将根目录的纯文档文件 `README.md` 和 `README.en.md` 错误地纳入了应用镜像路径校验流程，判定两个文件不符合 appstore 映像路径规范（要求路径格式为 `/README.md`）。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下两个纯文档文件（`README.md` 和 `README.en.md`）中的镜像标签信息（新增 24.03-lts-sp3、25.09 条目，调整排序），未涉及任何 Dockerfile、meta.yml、image-list.yml 等应用镜像构建文件。CI 失败与 PR 改动内容**无关**——CI 的 appstore 校验逻辑在检测到 diff 包含根目录 README 文件时，错误地将其视为待上架的应用相关文件，触发了路径格式校验。这是 CI 基础设施/校验工具本身的缺陷，并非 PR 代码引入的问题。

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `update.py` 的 appstore 规范校验需要增加白名单/过滤逻辑，排除仓库根目录的纯文档文件（如 `README.md`、`README.en.md`、`CONTRIBUTING.md` 等），使其不被纳入应用镜像路径校验的检查范围。这属于 CI 基础设施侧的修复，无需在此 PR 中做任何代码改动。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中第 273 行附近的 spec 校验逻辑具体如何判定哪些文件需要走路径检查，以及是否存在可配置的排除列表。
- 此 CI 校验是否在其他项目中已存在同类误报（参考历史 PR #2512 中 `.claude/README.md` 等元数据目录文档的同类路径校验失败问题），以确认是否需要从 CI 工具层面统一修复。

## 修复验证要求
（不适用——此为 CI 基础设施问题，无需 PR 侧代码修复。code-fixer 无需对此 PR 进行任何修改。）

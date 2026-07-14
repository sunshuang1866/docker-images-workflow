# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式11（CI appstore 路径校验失败）

## 根因分析

### 直接错误
```
2026-07-12 15:33:08,211-INFO: Difference: [
    "README.en.md",
    "README.md"
]
...
2026-07-12 15:33:13,075-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
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
- 失败原因: CI 管道的 appstore 发布规范校验工具（`update.py`）对仅包含文档变更的 PR 错误触发了路径校验。该 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 来更新可用基础镜像标签列表，这些是项目级文档文件，而非 appstore 镜像提交。校验工具将其视为 appstore 发布条目进行路径合规检查，因不符合 appstore 路径规范而报错。

### 与 PR 变更的关联
与 PR 变更无因果关系。PR 仅更新了两个根目录级 README 文件中的基础镜像标签文档，不涉及任何应用镜像 Dockerfile、meta.yml 或 image-info.yml 等 appstore 发布相关文件。CI 管道的 appstore 校验对文档类变更是误报。

## 修复方向

### 方向 1（置信度: 高）
CI 管道的 appstore 发布规范校验应在检测到变更文件仅包含非 appstore 路径的文件（如根目录 README）时自动跳过该校验。可在 `update.py` 中加入变更文件类型/路径过滤逻辑，对不在 `AI/`、`Bigdata/`、`Cloud/` 等应用镜像场景目录下的文件，不执行 appstore 路径规范检查。

### 方向 2（置信度: 中）
如果 CI 不允许修改校验逻辑，则需确认该 PR 是否需要单独触发忽略 appstore 检查的标志（如 PR 标签、commit message 关键字等），或将文档变更与代码变更拆分为独立 PR（文档 PR 不走 appstore 校验流水线）。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑是否硬编码了所有变更文件都必须通过 appstore 路径校验，还是存在白名单/跳过机制。
- 同类仓库中是否已有文档 PR 成功通过 CI 的先例，若有，其触发方式（如标签、提交信息格式）是否与本 PR 不同。

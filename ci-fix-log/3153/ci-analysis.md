# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: "文档变更误触发appstore校验"
- 新模式症状关键词: "appstore, Path Error, expected path, README.md, update.py"

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
...
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具 (`update.py`) 对仅有的 PR 变更文件 `README.md` 执行了路径校验。`README.md` 位于仓库根目录，不属于任何 appstore 镜像目录，而该校验工具期望所有变更文件遵循 `/{category}/{image}/{version}/{os-version}/...` 的 appstore 目录结构。根目录文档文件不匹配该预期模式，被标记为路径错误。CI 日志中 `Difference: ["README.md"]` 表明该工具仅检测到 README.md 一个变更文件，并对其执行了校验。

### 与 PR 变更的关联
PR 仅修改了两个仓库顶层文档文件（`README.md` 和 `README.en.md`），更新了 openEuler 基础镜像可用 tags 列表：新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 四个条目，并将 `latest` 对应的链接 URL 修正为 `/openEuler-24.03-LTS-SP4/docker_img/`。变更内容仅为文档元数据的增补与修正，不涉及任何 Dockerfile、应用镜像构建或 appstore 上架相关文件。CI 失败由 appstore 校验工具对纯文档类 PR 的错误触发引起，与 PR 的实际变更内容无关。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 校验工具 (`update.py`) 应在文件列表过滤阶段增加白名单/跳过逻辑：当扫描到的变更文件仅为仓库根目录的文档文件（如 `README.md`、`README.en.md`、`LICENSE` 等），且无任何 appstore 镜像目录内的变更时，直接跳过 appstore 路径规范校验并返回成功。此修复需在 CI 工具端代码中实现，不涉及本 PR 的文件变更。

### 方向 2（置信度: 低）
若 CI 工具不可修改，则需在 CI 流水线定义中增加条件分支：在触发 appstore 校验步骤前，先检查变更文件列表是否包含 appstore 镜像目录路径（满足 `{category}/{image}/{version}/{os-version}/` 模式），若无则跳过该校验步骤。

## 需要进一步确认的点
1. CI 日志中上游触发器显示的 PR 编号为 3184（`PR 3184 [sunshuang1866:fix/3153 -> master]`），而本分析目标 PR 编号为 3153。需确认 3184 是否为 CI 编排层生成的内部编号，以及该日志确实对应 PR #3153 的运行。
2. `eulerpublisher/update/container/app/update.py` 第 273 行前后的校验逻辑：是如何从 `Difference: ["README.md"]` 走到 `[Path Error]` 判定，以及是否有针对根目录文件的早期跳过/豁免条件。
3. 仓库历史中是否有纯文档变更 PR（如 README 修正）成功通过 CI 的先例，以佐证本次为偶发性 CI 工具误判。

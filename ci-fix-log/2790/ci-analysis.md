# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录文件被appstore校验拦截
- 新模式症状关键词: Path Error, The expected path should be, appstore, update.py, README.md

## 根因分析

### 直接错误
```
2026-06-30 11:28:03,983-.../update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
2026-06-30 11:28:09,089-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具 (`update.py`) 对本次 PR 中变更的 `README.md` 和 `README.en.md` 两文件执行路径校验，均判定为 FAILURE。该校验逻辑原本用于检查镜像目录下的文件（如 Dockerfile、meta.yml 等）是否符合 appstore 上架规范，但根目录的 README 文件并非镜像相关提交，被校验工具误判为路径不合规。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（新增 24.03-lts-sp3、25.09 等镜像 tag 条目，调整已有 tag 顺序），**不涉及任何镜像构建相关文件**（无 Dockerfile、meta.yml、image-list.yml 变更）。CI 流水线中集成的 appstore 发布规范检查将这两个纯粹的文档文件误纳入镜像上架校验范围，导致路径校验失败。**本次 CI 失败与 PR 代码变更内容无关，属于 CI 流程问题。**

## 修复方向

### 方向 1（置信度: 中）
CI 流水线（`eulerpublisher/update/container/app/update.py`）的 appstore 校验逻辑在识别变更文件后应排除仓库根目录的文档文件（如 `README.md`、`README.en.md`、`LICENSE` 等），仅对镜像目录内的文件执行路径和格式校验。需在 `update.py` 的文件过滤阶段增加根目录文档文件的豁免逻辑。

### 方向 2（置信度: 低）
如果该 CI 流水线本不应被纯文档 PR 触发，可在 trigger 层（`multiarch/openeuler/trigger/openeuler-docker-images`）增加 PR diff 文件类型过滤：当变更仅涉及 Markdown 文档且不含镜像构建文件时，跳过下游 x86-64/aarch64 构建 job，避免触发不必要的 appstore 校验。

## 需要进一步确认的点
1. `update.py:273` 处的路径校验逻辑是否可配置豁免列表，以及当前是否有针对根目录文件的豁免规则。
2. 该 CI 流水线是否有机制区分"镜像提交 PR"和"纯文档 PR"，或两者的 trigger 条件是否相同。
3. 是否已有其他纯 README 修改的 PR 遭遇同类 CI 问题，以确认这是回归还是长期存在的已知行为。

## 修复验证要求
若修复方向 1 涉及修改 `eulerpublisher` 仓库中的 `update.py`，code-fixer 须确认：
- 在本地用包含根目录 README 变更的测试 PR，验证修改后的 `update.py` 能正确豁免根目录文件且不影响正常的镜像路径校验。
- 若 `update.py` 不在本仓库而在独立的 `eulerpublisher` 仓库中，需确认变更提交到正确的仓库。

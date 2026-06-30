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
2026-06-30 11:28:09,089-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```
```
2026-06-30 11:28:03,983-.../update.py[line:356]-INFO: Difference: [
    "README.en.md",
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 PR 修改了仓库根目录下的 `README.md` 和 `README.en.md`，将这两个文件纳入路径校验范围，判定它们不符合 appstore 镜像目录的路径规范（期望路径应为 `/{image-name}/README.md` 等镜像子目录格式），导致路径校验失败。

### 与 PR 变更的关联
PR 仅修改了两个仓库根目录下的 README 文件（`README.md` 和 `README.en.md`），变更内容为更新"可用镜像 Tags"列表：新增 `24.03-lts-sp3`、`25.09` 条目，拆分 `24.03-lts-sp2` 为独立条目并修正其错误的 URL（原来指向 SP1 路径）。这些是纯文档说明更新，不涉及任何 Dockerfile、镜像构建、测试代码或元数据文件的修改。CI 失败并非 PR 内容有误，而是 CI 校验工具 (`update.py`) 将所有 diff 中的文件一律按 appstore 镜像发布规范进行路径校验，仓库根目录 README 文件不在该规范覆盖范围内，导致误报。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `eulerpublisher/update/container/app/update.py` 在收集 PR diff 文件并进行 appstore 路径校验时，未排除仓库根目录下的项目级 README 文件（`README.md`、`README.en.md`）。需要在工具的 diff 文件收集或校验逻辑中增加过滤条件，将仓库根目录 README 文件排除在 appstore 路径校验范围之外。PR 本身的文档改动是正确且无害的，无需任何修改。

### 方向 2（置信度: 低）
如果 CI 校验工具的设计意图确实是"PR 中任何非镜像目录的文件变更都会触发失败"，则 README 文档更新需要通过其他渠道（如直接在 master 分支提交、或通过其他不受此工具拦截的 PR 流程）完成。当前 PR 可被合并不影响任何镜像构建。

## 需要进一步确认的点
- 确认 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现，查明其是否对仓库根目录文件有特殊的排除规则（如果已有排除规则但未生效，则为工具 bug）
- 确认本次 CI 流程中下游架构构建 job（如 aarch64）是否也因同类原因失败，或是否另有其他错误
- 确认该 PR 是否确实需要触发 CI appstore 校验流程（纯 README 文档更新理论上不需要），是否存在 trigger 阶段的 job 过滤逻辑可以优化

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——本失败不涉及对外部源文件的修改）

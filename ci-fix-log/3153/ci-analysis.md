# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（CI appstore 路径校验失败）
- 新模式标题: (无，已匹配现有模式)
- 新模式症状关键词: (无)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范校验工具（`update.py`）检测到 `README.md` 被修改，进行了路径校验，报告 "[Path Error] The expected path should be /README.md"。但 `README.md` 已位于仓库根目录 `/README.md`，实际路径与"预期路径"一致。推测 CI 校验工具在处理相对路径 `README.md` 与绝对路径 `/README.md` 的比较时存在路径规范化问题（缺少前导 `/` 导致字符串匹配失败）。

### 与 PR 变更的关联
- **与 PR 变更无关**。PR 仅修改了仓库根目录的 `README.md` 和 `README.en.md`，更新了基础镜像的可用 tags 列表（增加 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目，调整 latest 指向）。这是纯文档更新，不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-info.yml 变更。
- CI 的 appstore 发布规范校验可能对所有触发 `merge_request` 的 PR 执行，但该校验逻辑并不适用于根目录级别 README 文档变更的场景——此 PR 无意于发布任何应用到 appstore。

## 修复方向

### 方向 1（置信度: 中）
CI 校验工具 `update.py:273` 在处理变更文件路径时，存在相对路径与绝对路径的规范化差异。若校验工具期望文件路径以绝对路径形式（`/README.md`）出现，但 diff 提取的路径为相对路径（`README.md`），则需在 `update.py` 中统一路径格式（如对所有检查项路径添加前导 `/`）或放宽根目录级别 README 文件的校验规则（跳过非应用镜像目录下的 README 变更）。

### 方向 2（置信度: 低）
若校验工具的行为是设计如此（即不允许仅通过修改根目录 README 来触发 CI appstore 检查流水线），则可能需要在 upstream trigger 层面对该类纯文档 PR 提前过滤——在进入 `x86-64` 下游构建 job 前判断变更是否仅涉及根目录非镜像文件，避免触发无意义的 appstore 规范检查。

## 需要进一步确认的点
1. **`update.py` 的路径校验逻辑**：需要查阅 `eulerpublisher/update/container/app/update.py` 第 273 行附近的 `check_path` / `validate_path` 逻辑，确认路径比较时是否存在相对路径 vs 绝对路径的规范化遗漏。
2. **trigger 层的 PR 过滤机制**：确认上游 trigger job 是否对所有 `merge_request` 事件无差别地触发下游 appstore 校验 job，还是已有过滤逻辑但未生效。
3. **是否为已知上游 CI 工具 bug**：检查 `update.py` 相关代码近期的提交历史，确认这是一个已知的路径匹配问题（类似模式11中 PR #2512 的聚类案例）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无。本次失败不涉及对外部上游源文件的正则匹配或 patch 操作。

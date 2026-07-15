# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: Appstore 路径校验误触发
- 新模式症状关键词: Path Error, expected path, appstore, README.md, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（eulerpublisher）检测到 PR 修改了仓库根目录的 `README.md`，并对其执行了 appstore 发布路径校验。该校验期望文件路径格式为 `/README.md`（带前导 `/`），但工具内部将根目录文件表示为 `README.md`（无前导 `/`），导致路径校验判定为 FAILURE。

### 与 PR 变更的关联
**与 PR 变更无实质关联。** 本 PR 仅修改了仓库根目录的两个 README 文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 Tag 列表（将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09` 等标签条目）。PR 不涉及任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 或应用镜像文件的新增与修改。CI 失败是因为 appstore 发布规范预检工具对所有修改了文件的 PR 均执行路径校验，而文档类 PR 不应触发该检查。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher` 的 appstore 发布规范预检逻辑需要改进：对于仅修改仓库根目录 README（不含任何应用镜像文件）的 PR，应跳过 appstore 路径校验，避免误报。具体修改应在 `eulerpublisher/update/container/app/update.py` 中增加判断逻辑，过滤掉非应用镜像相关的文件变更。

### 方向 2（置信度: 低）
若 CI 工具短期内无法修改，可考虑通过 Jenkins 流水线配置层面的调整，使 appstore 预检步骤仅在 PR 包含应用镜像路径下的文件变更时才触发，而非对所有 PR 均执行。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py` 中 `line:273` 附近的路径校验逻辑具体实现，以明确为何 `README.md`（根目录文件）会被纳入 appstore 发布规范检查范围。
2. 确认 Jenkins 流水线配置中 appstore 预检步骤的触发条件，是否存在可配置的文件路径过滤规则。
3. 确认历史类似场景（纯文档 PR 触发 appstore 路径校验）是否有标准处理流程或已知 workaround。

## 修复验证要求
此失败归类为 `infra-error`，根因在 CI 工具（eulerpublisher）而非 PR 代码变更。若 code-fixer 采取方向 1 修复，需修改 `eulerpublisher` 工具源码并确保该修复不会导致真正的 appstore 发布 PR 跳过必要的路径校验；若采取方向 2，需在 Jenkins pipeline 中调整触发条件并验证仅修改根目录 README 的 PR 不再触发 appstore 预检。

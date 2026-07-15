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
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具（`update.py`）检测到仓库根目录下的 `README.md` 文件被修改，对其执行路径校验时报 `[Path Error] The expected path should be /README.md`。该工具路径比较逻辑可能存在前导 `/` 缺失导致的不匹配，或该工具对根级文档文件变更触发了误报。

### 与 PR 变更的关联
**与 PR 代码变更无实质性关联。** PR #2790 仅修改了仓库根目录下的两个 README 文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 Tags 列表：
- 将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`（同时修正了 URL 中 `SP1`→`SP3` 的错误）
- 新增 `25.09` 和 `24.03-lts-sp2` 条目
- 这些是纯文档内容更新，不涉及任何 Dockerfile、构建脚本或镜像元数据文件

CI 的 `eulerpublisher` appstore 校验工具对根级 README 文件变更触发了路径检查，并判定为 FAILURE。这是 CI 工具行为导致的问题，而非 PR 变更引入了代码错误。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题（infra-error），与 PR 代码变更无关。PR #2790 的 README 文档更新本身是正确的，不应被 appstore 路径校验阻断。建议：
- CI 团队确认 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑是否需要排除仓库根级文档文件（如 `README.md`、`README.en.md`）的变更
- 或确认路径比较时是否需要补充前导 `/` 以统一路径格式

### 方向 2（置信度: 低）
如果 appstore 发布流程确实不允许修改根级 README 文件，则需考虑将 Tags 更新内容移入 `Base/openeuler/` 等镜像专属目录的文档中，而非仓库根级 README。但从业务合理性来看，根级 README 作为项目整体文档应当允许独立更新。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py:273` 前后文的路径校验逻辑具体实现，确认是精确字符串比较还是存在路径归一化步骤
2. CI 的 appstore 校验是否应将仓库根目录下的项目级文档（`README.md`、`README.en.md`）排除在校验范围之外
3. 是否有其他仅修改根级文档的 PR 也遇到同类问题，以确认是否为已知的 CI 工具缺陷

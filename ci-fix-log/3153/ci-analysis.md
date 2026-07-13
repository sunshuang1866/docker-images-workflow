# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录文档路径校验失败
- 新模式症状关键词: Path Error, expected path should be, README, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-12 15:33:13,075 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范校验工具对 PR 变更的根目录文档文件（`README.en.md` 和 `README.md`）执行路径校验，期望路径为 `/README.md`。`README.en.md` 不匹配预期路径直接失败；`README.md` 也因路径比对方式（可能缺少前导 `/` 归一化，或校验器仅识别 appstore 管理的特定路径）被标记为 FAILURE。

### 与 PR 变更的关联
PR 仅修改了仓库根目录的两个 README 文件（`README.md` 和 `README.en.md`），更新了可用的基础镜像 tag 列表。改动本身不涉及代码、构建脚本或 Dockerfile。CI 失败发生在 eulerpublisher 工具的 appstore 发布规范预检阶段（`update.py`），该检查将根目录文档文件视为不合规路径。此失败**与 PR 的文档内容无关**，是 CI 工具对 root 级文档文件变更的路径校验策略问题。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具可能不预期仓库根目录的 README 文件在 PR 中被单独修改。若该 PR 仅需更新文档而不涉及镜像发布，可通过调整 CI 触发条件（如仅当变更涉及 `Bigdata/`、`AI/` 等镜像目录时才触发 appstore 路径校验）来绕过此检查。

### 方向 2（置信度: 低）
`update.py` 中的路径比对逻辑可能存在缺陷，例如对相对路径 `README.md` 与绝对路径 `/README.md` 未做归一化处理，导致合法路径也被误报。若确认该点是根因，可在 `update.py` 的路径校验函数中增加路径归一化逻辑。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑：确认校验器是否将 `README.md`（相对路径）与 `/README.md`（绝对路径）视为不同值，导致原本合法的文件也被误报。
2. 该 CI pipeline 的 appstore 预检步骤是否针对所有 PR 触发，还是仅对触及特定目录的 PR 触发——若为前者，纯文档 PR 理应被排除在检查范围之外。
3. 确认 `README.en.md` 是否在 appstore 规范的允许文件白名单中，若不在，是否应将其加入白名单或排除根目录文档的检查。

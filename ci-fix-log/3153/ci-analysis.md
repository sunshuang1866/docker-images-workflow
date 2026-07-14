# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误——appstore 路径校验）
- 新模式标题: 根README路径校验异常
- 新模式症状关键词: Path Error, expected path, README.md, update.py, appstore

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839 - update.py[line:273] - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 的 appstore 路径校验工具对仓库根目录的 `README.md` 执行路径检查时，认为实际路径与预期路径 `/README.md` 不匹配。而 `README.md` 实际就在仓库根目录 `/README.md`，**实际路径与预期路径一致**，该失败是 CI 工具自身的路径规范化/匹配逻辑 bug 所致。

### 与 PR 变更的关联
**与 PR 内容无关。** 本次 PR 仅修改了两个文档文件（`README.md` 和 `README.en.md`），更新了 openEuler 基础镜像的可用 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2 条目）。未修改任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 或其他与应用镜像构建/发布相关的文件。CI 失败发生在 appstore 发布规范预检阶段，该预检对所有 PR 的变更文件执行路径校验，与 README 的具体内容无关。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施问题（eulerpublisher 工具对根目录 README.md 的路径匹配 bug），**Code Fixer 无需处理此 PR 的代码**。应通知 CI 维护团队排查 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑，检查为何 `/README.md`（实际路径）与 `README.md`（diff 中的相对路径）在校验中产生不匹配。

### 方向 2（置信度: 低）
若 CI 工具的逻辑是：所有出现在 diff 中的文件都必须能匹配到某个已注册的应用镜像路径，而根目录 README.md 不属于任何应用镜像目录，因此被标记为路径错误。这种情况需 CI 工具增加对仓库根目录文档文件（如 README.md、README.en.md）的白名单豁免逻辑。

## 需要进一步确认的点
1. `<redacted>/eulerpublisher/update/container/app/update.py` 中 `line:273` 附近的具体路径校验逻辑——是路径字符串匹配（`/README.md` vs `README.md`）还是应用镜像目录树校验。
2. CI 工具将 `README.md` 列为 "Check Item" 的原因：是否对所有 diff 中的文件都执行 appstore 路径校验。
3. 仅 `README.md` 被标记为失败而 `README.en.md` 未被标记的原因（日志中 Difference 只列出了 `README.md`）。

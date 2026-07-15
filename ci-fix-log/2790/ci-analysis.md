# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级文档路径校验误报
- 新模式症状关键词: Path Error, expected path should be, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 `README.md` 发生变更，对其执行镜像级别路径校验，但仓库根目录的 `README.md` 是项目级文档而非应用镜像文档，其路径格式不满足 appstore 镜像目录结构规范，导致误报为 FAILURE。

### 与 PR 变更的关联
- PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`，变更内容为更新镜像 Tag 列表（新增 24.03-lts-sp3、25.09 条目，修正过期 URL）。这些是纯粹的文档内容更新。
- CI 工具通过 git diff 检测到 `README.md` 变更后，将其纳入 appstore 发布规范校验流程。因 `README.md` 位于仓库根目录而非应用镜像子目录结构内（如 `AI/<image>/README.md`），校验工具的路径正则/匹配规则将其判定为路径不合规。
- **该失败与 PR 改动内容本身无关**，任何修改根级 `README.md` 的 PR 都会触发同样的误报。变更内容（Tag 列表更新）本身是正确合理的。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）需排除仓库根目录级别的非镜像文件。在 diff 检测阶段或路径校验阶段，应将仓库根目录的 `README.md`、`README.en.md` 等项目级文档从 appstore 镜像路径校验范围中排除，避免误报。类似历史案例见于 PR #2512（`.claude/README.md` 路径校验误报）。

### 方向 2（置信度: 低）
若 CI 工具路径校验本身无问题，而是路径解析归一化导致相对路径 `README.md` 与绝对路径 `/README.md` 比对不匹配，则需在工具中统一路径解析格式（如在比较前对两者做 `os.path.normpath` 或添加一致性前缀处理）。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现：是对所有 diff 文件做校验，还是仅校验符合特定路径模式的镜像文件。需查阅 `update.py` 第 273 行附近的 `_verify_specification` 或 `_check_path` 相关方法，确认 `"The expected path should be /README.md"` 的生成逻辑。
- 确认 `README.en.md` 为何未被一同标记为 FAILURE（可能是工具仅校验特定后缀如 `README.md`，或 diff 阶段已过滤掉 `.en.md`）。
- 确认历史版本中 root README.md 的修改是否也触发过相同校验失败（可检索 CI 历史记录中的同类型误报）。

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 根目录README误触appstore校验
- 新模式症状关键词: Path Error, expected path should be, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 本身的校验工具，非 PR 代码）
- 失败原因: CI 的 `eulerpublisher` appstore 发布规范校验工具检测到 PR 修改了 `README.md`，并对其实施路径合规检查。`README.md` 位于仓库根目录（`/README.md`），校验工具报 `[Path Error] The expected path should be /README.md` ——该错误信息存在自相矛盾（文件实际路径即 `/README.md`，与"期望路径"一致），疑为 CI 工具对根目录级 `README.md` 的路径匹配逻辑存在缺陷或边界条件处理不当，导致为纯文档类 PR 产生误报。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新基础镜像可用 tags 列表），属于纯文档变更，不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-list.yml。CI 的 appstore 发布校验本不应适用于仓库根目录的文档文件，由于校验工具对所有修改过的 `README.md` 无差别执行路径检查而误报。

## 修复方向

### 方向 1（置信度: 中）
**CI 工具侧修复**：修改 `eulerpublisher/update/container/app/update.py` 中的路径检查逻辑，对仓库根目录（`/README.md`）添加豁免或特殊处理，使其不进入 appstore 发布规范校验流程。根目录 README 是仓库级文档，不遵循应用镜像的目录层级规范。

### 方向 2（置信度: 低）
若 CI 工具的行为符合预期（根目录 README.md 确实需要遵守 appstore 发布规范），则需要确认根目录 README.md 应满足何种特定格式/路径结构才能通过校验。但目前日志中"期望路径为 /README.md"与实际路径完全一致仍报错的矛盾，强烈暗示这是 CI 工具的 bug 而非内容格式问题。

## 需要进一步确认的点
1. **获取 eulerpublisher 源码**：需要查看 `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑，确定其对根目录 README.md 的处理方式。
2. **确认 CI 设计意图**：根目录 `README.md` 的修改是否预期进入 appstore 发布规范校验？如果否，则应在 CI 工具中添加文件路径过滤。
3. **复现验证**：可尝试提交一个仅修改根目录 README.md 的 PR 来确认该 CI 检查是否稳定触发。
4. **PR 分支路由**：日志头部显示 `PR 3184 [sunshuang1866:fix/3153 -> master]`，存在 PR 编号不一致（3184 vs 3153），需确认 CI 是否正确关联了本次 PR 的上下文。

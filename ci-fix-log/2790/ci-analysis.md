# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发应用市场检查
- 新模式症状关键词: Path Error, expected path, appstore, README.md, update.py, specification errors

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（`update.py` 中的规范校验函数）
- 失败原因: CI 的应用市场（appstore）发布规范预检流水线被一个纯文档类 PR 误触发。该 PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（更新支持的镜像 Tag 列表），不含任何 Dockerfile、meta.yml、image-info.yml 等应用镜像发布必需的构建文件。`eulerpublisher` 工具的路径校验逻辑将根级 `README.md` 视为无效的应用市场发布路径，报告 `[Path Error]`。

### 与 PR 变更的关联
PR 变更仅涉及两个根级 README 文件的 Tag 列表更新：
- 将 `24.03-lts-sp2, 24.03, latest` 改为 `24.03-lts-sp3, 24.03, latest`
- 新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目
- 修正了原先指向 `SP1/docker_img/` 的 `latest` 链接

这些变更是合法的文档维护操作，并未引入代码缺陷。CI 失败是因为该 PR 被路由到了面向应用镜像发布的 `eulerpublisher` 校验流水线，而根级 README 不在应用市场（appstore）发布规范的预期路径范围（预期路径格式为 `{category}/{image}/{version}/{os-version}/`）。

**注意**：diff 中 `24.03-lts-sp3` 条目出现了两次（一次在 `latest` 行，一次在独立行），属于内容冗余但非 CI 失败原因。

## 修复方向

### 方向 1（置信度: 中）
跳过或关闭该 PR 的应用市场发布校验。若该 PR 的目标仅为更新项目根级 README 文档，则需确保 CI trigger 不会将纯文档类 PR 路由至 `eulerpublisher` 的应用市场发布检查流水线。这属于 CI 流水线配置层面的调整。

### 方向 2（置信度: 低）
若 CI 流水线要求所有 PR 都通过应用市场检查，则此 PR 应补充一个有效的应用镜像发布内容（如新增/修改某个分类下的 Dockerfile、meta.yml 等），或将 `README.md` 的变更合并到另一个已包含应用镜像发布的 PR 中。

## 需要进一步确认的点
1. CI 流水线（`multiarch/openeuler/trigger/openeuler-docker-images`）是否应只对包含 `meta.yml` 或 `Dockerfile` 变更的 PR 触发 appstore 检查，而非对所有 merge_request 事件触发。
2. Diff 中 `24.03-lts-sp3` 重复条目（同一镜像 Tag 出现两次）是有意的还是笔误——建议确认是否需要去重。
3. `README.en.md` 同样有变更但 CI diff 检测（`update.py:356`）仅报告了 `README.md`，需确认 `README.en.md` 是否未被纳入检查范围还是被遗漏。

# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 根README误触发appstore校验
- 新模式症状关键词: Path Error, expected path, README.md, appstore, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 的 `eulerpublisher` 工具 `update.py:273`（appstore 发布规范预检）
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（文档内容更新），但 CI 的 appstore 校验工具 `eulerpublisher` 将根目录的 `README.md` 误识别为需要发布到应用商店的镜像文件，对其执行镜像路径校验，导致校验失败——根目录 `/README.md` 不是合法的应用镜像 README 路径（应为 `{category}/{image}/{version}/{os-version}/README.md` 等形式）。

### 与 PR 变更的关联
PR 的变更仅为 `README.md` 和 `README.en.md` 的文档内容更新（新增/调整可用镜像 Tags 列表和链接）。此次改动不涉及任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 等镜像构建文件。CI 失败是由 appstore 校验工具对不应校验的根文档文件触发了路径检查，属于 CI 工具的过检行为，**与 PR 变更内容本身无关**。

## 修复方向

### 方向 1（置信度: 高）
CI 的 eulerpublisher 工具需要在 appstore 发布规范预检阶段排除仓库根目录的文档文件（`README.md`、`README.en.md`），不应将这类仓库级文档文件纳入应用镜像路径校验。修复应在 `eulerpublisher` 工具侧实现文件过滤逻辑，而非修改本 PR 内容。

## 需要进一步确认的点
- 本次 CI 运行由上游 trigger job (`multiarch/openeuler/trigger/openeuler-docker-images` build #2783) 触发，触发引用为 PR #3194 (`[sunshuang1866:fix/2790 -> master]`)，而非 PR #2790。需确认 PR #3194 的变更范围是否与本分析中的 PR #2790 diff 一致，或是否包含额外的镜像文件变更。
- `eulerpublisher` 工具的 appstore 校验逻辑（`update.py:273`）中的文件过滤规则具体实现，确认是否需要增加对根目录 README 类文件的排除处理。

## 修复验证要求
（无——本次失败为 infra-error，无需对 PR 文件或正则表达式进行修改。）

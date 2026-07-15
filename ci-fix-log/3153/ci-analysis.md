# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（但存在差异，见下方分析）
- 新模式标题: （不适用 — 已有模式可参考但非完全匹配）

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范校验工具）
- 失败原因: CI 的 appstore 发布规范校验工具（`eulerpublisher`）检测到 `README.md` 发生了变化，并对其执行了 appstore 路径规范校验。但仓库根目录的 `README.md` 并非某个应用镜像的入口文件，不适用 appstore 的路径规范（期望路径格式为 `{category}/{app}/{version}/{os-version}/README.md`），导致校验失败。

### 与 PR 变更的关联
**PR 与失败无关。** 本次 PR 仅修改了两个根目录文档文件：
- `README.md`：更新基础镜像可用 Tags 列表（将默认 latest 标签从 `24.03-lts-sp2`/SP1 链接更新为 `24.03-lts-sp4`/SP4 链接，新增 `sp3`、`25.09`、`sp2` 条目）
- `README.en.md`：同上英文版

PR 未涉及任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 或应用镜像目录结构的变更。CI appstore 校验工具将根目录 `README.md` 纳入校验范围属于过度校验。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题 —— appstore 校验工具 `eulerpublisher/update/container/app/update.py` 应将校验范围限定在 `image-list.yml` 中注册的应用镜像目录内，排除仓库根目录的文档文件（`/README.md`、`/README.en.md`）。此为 CI 工具/平台的配置或代码调整，不涉及 PR 的 Dockerfile 或应用镜像代码修改。

### 方向 2（置信度: 低）
若 CI 工具确实有意对所有变更的 `README.md` 进行 appstore 路径校验（即便在仓库根目录），则需确认该工具的最新版本是否需要根目录 `README.md` 满足某种未文档化的规范要求（如必须保持特定 markdown 结构或 meta 注释头）。但鉴于错误信息明确为 "Path Error" 而非内容格式错误，此方向可能性较低。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中触发 path validation 的逻辑 —— 它是否会将所有变更的 `README.md` 文件都纳入 appstore 规范检查，还是仅检查 `image-list.yml` 中注册的目录？
2. 同一 CI 工具的历史行为：纯文档类 PR（仅修改根目录 README 文件）此前是否能通过 CI？若能通过，说明是 CI 工具近期变更引入了过度校验。
3. 日志中的 PR 编号不一致：日志显示由 "PR 3184 [sunshuang1866:fix/3153 -> master]" 触发，但实际分析的 PR 为 #3153。PR #3184 可能是针对此问题的修复尝试分支。需确认 CI 测试的是哪个分支的实际变更。

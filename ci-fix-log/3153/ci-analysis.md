# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
  There are some specification errors for releasing on appstore in this PR, please check as above.

+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具 appstore 发布规范预检）
- 失败原因: CI 预检工具检测到 PR 修改了根级 `README.md`，对该文件执行 appstore 发布规范校验时报告"Path Error: The expected path should be /README.md"。但该文件本身即位于仓库根目录（`/README.md`），路径实际符合要求。错误可能源于：① README.md 缺少 appstore 发布规范要求的元数据头（如 Copyright + SPDX 声明，见模式17），CI 工具将内容格式错误归类为"Path Error"；② CI 工具在处理 fork（`sunshuang1866`）克隆路径时存在路径解析偏差。

### 与 PR 变更的关联
PR 仅修改两个根级文档文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2，移除旧的 24.03-lts-sp2/latest 映射）。这是纯文档变更，不涉及任何 Dockerfile、构建脚本或元数据文件的修改。CI 预检工具将一次文档 PR 错误地路由到了 appstore 发布规范校验流程，导致校验失败。

## 修复方向

### 方向 1（置信度: 中）
CI 工具对根级 `README.md` 的 appstore 发布规范校验路径解析有误。根级 README 本身不应对应任何具体的 appstore 应用镜像条目，应被排除在 appstore 发布规范检查之外。Code-fixer 无需对 PR 内容做任何修改；这属于 CI 工具侧（`eulerpublisher/update/container/app/update.py`）的检查逻辑问题，需由 CI 维护团队将根级 `README.md` 和 `README.en.md` 加入 appstore 检查的白名单过滤条件。

### 方向 2（置信度: 低）
如果 CI 工具有意对根级 README.md 执行规范校验，则失败原因可能是文件缺少必需的 Copyright + SPDX 头（参照模式17）。此方向置信度低，因为错误类型明确为"Path Error"而非内容格式错误，且根级 README 本身已有 Community 级别的 Copyright 申明格式，未必适用 appstore 的 MulanPSL-2.0 许可证头模板。

## 需要进一步确认的点
1. **CI 工具逻辑确认**：需查阅 `eulerpublisher/update/container/app/update.py:273` 及附近的 `_check_*` 方法的源码，确认"Path Error"的具体检查条件——是纯路径匹配还是包含内容/元数据检查，以及是否已对根级文件做了过滤。
2. **PR 分支与 master 的差异确认**：需确认 `sunshuang1866/openeuler-docker-images.git` 的 fork 克隆后，`README.md` 在 CI 工作目录下的实际路径是否为 `/README.md`（不带任何前缀目录层级）。
3. **是否为 CI 工具已知缺陷**：需确认同类纯文档 PR（只改根级 README）是否历史上也触发过同样的 appstore 路径校验失败。

## 修复验证要求
（不适用 — 本 PR 为纯文档修改，不涉及源码/正则/Dockerfile 变更。）

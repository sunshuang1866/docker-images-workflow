# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具对仓库根目录下的 `README.md` 路径校验失败。该工具期望路径格式为 `/README.md`（带前导 `/`），而 git diff 输出的路径为 `README.md`（无前导 `/`），导致路径格式匹配不通过。另一种可能是根目录 `README.md` 不属于任何应用镜像目录结构，CI 预检工具无法将其映射到 appstore 的预期路径规则中。

### 与 PR 变更的关联
本 PR 仅修改了两个文件（`README.md` 和 `README.en.md`），纯文档变更——更新基础镜像可用 tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09、24.03-lts-sp2，并将 latest 标签从 sp2 更新为 sp4）。CI 失败并非由 PR 代码内容导致，而是由 CI 预检工具（`eulerpublisher` 的 `update.py`）对根目录文件路径的表征方式与 git diff 输出的路径格式不一致所引发。

值得注意的是，日志中记录的差异文件仅包含 `README.md`，而 `README.en.md` 未被检查工具列出，说明该检查可能仅针对特定文件类型或仅有 `README.md` 触发了路径规则匹配。

## 修复方向

### 方向 1（置信度: 低）
CI 预检工具（`eulerpublisher/update/container/app/update.py`）中的路径匹配逻辑存在缺陷，对根目录文件的路径归一化处理不统一（`README.md` vs `/README.md`）。需要 CI 平台管理员/工具维护者在 `update.py` 的路径比较逻辑中添加路径归一化（如统一添加或移除前导 `/`），使 git diff 输出的相对路径能与工具内部的绝对路径预期匹配。

**修复验证要求**：需查阅 `eulerpublisher/update/container/app/update.py` 源码中路径比较的具体实现，确认是否因缺少 `os.path.normpath` 或类似归一化处理导致根目录文件被误判。

### 方向 2（置信度: 低）
若根目录 `README.md` 确实不在 appstore 期望的目录清单中，可在仓库元数据配置（如 `image-list.yml` 或 CI 白名单）中将根目录文件标记为例外项，绕过 appstore 预检。但此方向可能性较低，因为 README.md 属于仓库基础文档，不应被 appstore 路径检查拦截。

## 需要进一步确认的点
1. **`eulerpublisher/update/container/app/update.py` 路径比较逻辑**：确认第 273 行附近的路径检查逻辑，查明为何 `README.md` 与 `/README.md` 不匹配。
2. **`README.en.md` 为何未被检查**：`README.en.md` 也在 PR diff 中但未被 `Difference` 列表或 Check Items 表格提及，需确认检查工具的文件过滤规则。
3. **CI 日志中的 PR 编号不一致**：CI 日志显示 `PR 3184 [sunshuang1866:fix/3153 -> master]`，与上下文提供的 PR #3153 不一致。确认该次 CI 运行是否对应实际 PR #3153。

## 修复验证要求
本失败属于 infra-error，PR 本身的文档变更内容有效。若需修复 CI 工具，code-fixer 必须：
1. 从 `eulerpublisher` 仓库获取 `update/container/app/update.py` 源码，定位路径校验函数
2. 确认路径归一化逻辑后再提交修改

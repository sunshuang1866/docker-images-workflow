# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 路径格式不匹配
- 新模式症状关键词: Path Error, expected path should be, README.md, update.py, appstore specification

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 规范检查工具通过 `git diff` 检测到变更文件 `README.md`（无前导 `/` 的相对路径形式），但其内部的路径格式校验规则期望路径以 `/` 开头（即 `/README.md`）。两者格式不匹配，导致路径校验项失败。

### 与 PR 变更的关联
PR 变更仅涉及两个 README 文件的纯文档更新（在 `README.md` 和 `README.en.md` 中更新可用基础镜像的 Tags 列表）。变更内容本身无关构建、测试或应用镜像——无 Dockerfile、无 meta.yml、无 image-info.yml 变更。

该失败由 CI 工具（`eulerpublisher`）的路径解析/校验逻辑触发：只要 PR 修改了仓库根目录下的任何文件（包括 README），工具就会将其纳入 appstore 规范检查，而 `git diff` 返回的相对路径格式与工具内部期望的绝对路径格式不一致，导致校验失败。并非 PR 的文档内容有误。

## 修复方向

### 方向 1（置信度: 低）
CI 工具 `eulerpublisher/update/container/app/update.py` 第 273 行附近的 appstore 规范检查逻辑中，路径比较/校验环节可能未对 `git diff` 输出的相对路径做规范化处理（如添加前导 `/`），导致根目录文件被误判为路径格式错误。需审查该处路径校验实现，确认路径格式归一化逻辑是否正确。

### 方向 2（置信度: 低）
若 appstore 发布规范检查的设计意图是仅校验应用镜像目录下的文件（如 `Bigdata/`、`AI/` 等场景目录），则根级文档文件 `README.md` 不应被纳入检查范围。需确认 `update.py` 中变更文件列表的过滤逻辑是否遗漏了对仓库根级非镜像文件的排除。

## 需要进一步确认的点
1. **`update.py` 源码确认**：需要获取 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑（约第 260-280 行）的实际代码，确认路径比较时是否使用了硬编码的 `/` 前缀格式。
2. **上游仓库确认**：`eulerpublisher` 工具的源码仓库不在本 PR 中，需要从 CI 日志中的 clone 路径（`Cloning into 'eulerpublisher'...`）确认工具的版本及对应源码。
3. **历史成功案例分析**：确认此前修改根级 `README.md` 的 PR 是否也触发了相同校验（若是，则证明该检查与 PR 内容无关）。当前日志未能提供此信息。

## 修复验证要求
若修复方向涉及对 `eulerpublisher` 工具源码中路径校验逻辑的修改，code-fixer 必须：
1. 从 CI 日志中确认 `eulerpublisher` 工具的 clone 仓库地址和分支/commit。
2. 在对应源码中找到 `update.py` 第 273 行附近的路径校验逻辑。
3. 构造一个仅修改根级 README.md 的测试变更，验证修改后路径校验项不再失败。
4. 同时确保修改不影响 `Bigdata/`、`AI/` 等场景目录下文件的正常校验。

# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-update.py[line:356]-INFO: Difference: [ "README.md" ]
2026-07-14 15:28:07,685-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具 appstore 发布规范预检）
- 失败原因: CI 的 `eulerpublisher` 工具对 PR 中变更的文件运行 appstore 发布规范校验，对 `README.md` 报告 `[Path Error] The expected path should be /README.md`。然而 `README.md` 确实位于仓库根目录（diff 路径为 `a/README.md` → `b/README.md`），路径本身符合预期 `/README.md`。该验证失败可能是 CI 工具在克隆 fork 分支后做路径比较时存在字符串规范化不一致（如相对路径 `README.md` 与绝对路径 `/README.md` 的字符串匹配失败），或是 CI 环境工作目录导致的路径解析异常。

### 与 PR 变更的关联
PR #2790 仅修改了两个根级文档文件（`README.md` 和 `README.en.md`）中"可用镜像 Tags"部分的版本列表内容——将 `24.03-lts-sp2` 替换为 `24.03-lts-sp3`、新增 `25.09` 和 `24.03-lts-sp2` 条目、修正 URL 链接。**PR 未新增任何文件、未变更任何文件路径，也未涉及任何 Dockerfile 或构建逻辑**。CI 失败与 PR 的实际内容变更**无关**，属于 CI 基础设施层面的校验工具异常。

## 修复方向

### 方向 1（置信度: 中）
该失败为 CI 基础设施问题（`eulerpublisher` 工具对根级 `README.md` 的 appstore 路径校验出现误报），**与 PR 代码变更无关**，无需修改仓库文件。建议 CI 维护者排查 `update.py:273` 附近的路径比较逻辑，确认是否存在路径规范化缺失（如缺少对相对路径添加前缀 `/` 或 `os.path.normpath` 处理）。

### 方向 2（置信度: 低）
如果 CI 在克隆的 fork 分支中构建目录结构与主仓库不一致（如额外包裹了一层子目录），可能导致路径解析结果与预期不符。但日志显示 diff 检测到的变更文件仅为 `["README.md"]`，路径名称本身正确，此可能性较低。

## 需要进一步确认的点
1. **CI 工具源码**：`eulerpublisher/update/container/app/update.py:273` 附近的路径校验逻辑——具体是如何比较文件路径的（是否进行了 `os.path.normpath` 或 `lstrip('/')` 等规范化处理），以及为什么根级 `/README.md` 会触发 `[Path Error]`。
2. **fork 分支结构**：确认 `gitcode.com/sunshuang1866/openeuler-docker-images` 仓库中 `fix/2790` 分支的目录结构是否与主仓库完全一致，`README.md` 是否确实位于仓库根目录。
3. **是否为 CI 已知缺陷**：同类问题（CI appstore 路径校验对根级文件误报）是否在其他纯文档 PR 中也出现过。

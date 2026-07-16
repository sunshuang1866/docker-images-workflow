# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11（CI appstore 路径校验失败）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检）
- 失败原因: CI 预检工具 `eulerpublisher` 的 `update.py` 对 PR diff 中变更的 `README.md` 进行路径校验时，因路径格式不匹配（git diff 输出的路径为 `README.md`，不含前导 `/`，而 CI 工具期望的格式为 `/README.md`）导致 `[Path Error]` 校验失败

### 与 PR 变更的关联
PR 变更仅涉及两个根目录级文档文件的修改（`README.md` 和 `README.en.md`），更新了基础镜像可用 tag 列表（新增 sp4、sp3、25.09 等 tag）。变更内容本身**不会**触发任何构建或测试失败。失败发生在 CI 的 appstore 发布规范预检阶段，该预检工具对根目录 `README.md` 的路径格式进行了错误判断，与 PR 的实际代码改动无关。

值得注意的是，CI 日志中检测到的 changes 仅有 `README.md`，而 PR diff 中同时修改了 `README.en.md`，后者未被 CI 预检工具捕获（可能是因为该文件不在检查范围内）。

## 修复方向

### 方向 1（置信度: 中）
CI 编排工具 `eulerpublisher` 中的路径校验逻辑存在 bug，未能正确处理 git diff 输出中不含前导 `/` 的根目录文件路径。需要检查 `eulerpublisher/update/container/app/update.py` 中的路径比较逻辑，确保其对根目录文件的路径格式进行归一化处理（统一添加或移除前导 `/`），使 `README.md` 能匹配期望的 `/README.md`。

### 方向 2（置信度: 低）
CI 预检工具的设计可能本身不允许仅含文档变更的 PR 通过 appstore 发布检查（即 docs-only PR 被误判为需要发布）。如果这是预期行为，则需要调整 CI 策略，使纯文档类 PR 跳过 appstore 发布预检。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 的路径校验逻辑源码，确认路径比较时是否对 git diff 输出的路径做了前导 `/` 归一化
2. 该 CI 预检工具在其他 docs-only PR 中是否有同样的 false positive 表现（可对比同类历史记录验证是否为间歇性问题）
3. `README.en.md` 变更未被检测到的原因——是否该文件不在预检范围内，还是 splitter 工具过滤了该文件

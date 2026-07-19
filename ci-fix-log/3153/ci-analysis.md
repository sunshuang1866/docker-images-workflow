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
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 工具 appstore 发布规范预检）
- 失败原因: CI appstore 规范检查器对 PR 变更文件 `README.md` 进行路径校验时，将 git diff 输出的相对路径 `README.md` 与规范期值的绝对路径 `/README.md` 进行比较，未做路径归一化处理，导致路径格式不匹配判为失败。该文件实际位于仓库根目录 `/README.md`，符合预期位置，属于 CI 工具的路径比较缺陷。

### 与 PR 变更的关联
PR 仅修改了两个根目录文档文件（`README.md` 和 `README.en.md`），更新了基础镜像可用 tags 列表。触发 CI appstore 发布规范预检时，检查器对 `README.md` 变更文件执行路径校验，因路径格式不一致（相对路径 vs 绝对路径）判定失败。此失败与 PR 的文档内容变更本身无关，变更是合法且符合预期的。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 规范检查工具 `eulerpublisher/update/container/app/update.py` 中的路径比较逻辑缺少路径归一化（如统一添加或移除前导 `/`），导致仓库根目录文件的相对路径 `README.md` 与规范定义的绝对路径 `/README.md` 被错误判定为不匹配。修复方向：在 `update.py` 中增加路径归一化步骤，比较双方统一使用绝对路径格式。

### 方向 2（置信度: 低）
如果方向 1 不成立，另一种可能是 CI appstore 规范本身不允许在 appstore 发布 PR 中修改根目录 `README.md`（该文件属于项目级文档而非镜像级文档），CI 检查器的错误提示信息可能不够准确。若此为该检查项的预期行为，则本次 PR 的文档变更需要以独立于 appstore 发布的方式提交（如单独的 docs-only PR），需进一步确认 CI 规范中对根目录 `README.md` 修改的约束。

## 需要进一步确认的点
1. 查看 `eulerpublisher/update/container/app/update.py:273` 附近的路径比较逻辑，确认是否为路径归一化缺失导致的问题
2. 确认 CI appstore 发布规范是否允许在镜像发布 PR 中同时修改根目录 `README.md` 和 `README.en.md`
3. 日志中检测到的变更文件仅含 `README.md`，未包含 `README.en.md`，需确认 CI 工具的文件变更检测逻辑是否遗漏了 `README.en.md`
4. 日志来自 PR #3184（分支 `fix/3153`），需确认该修复 PR 的变更内容是否与 #3153 一致

## 修复验证要求
若修复方向 1 成立，需修改 `update.py` 中路径比较代码。code-fixer 在提交前应：
1. 从 eulerpublisher 对应版本仓库获取 `update.py` 的完整路径比较逻辑
2. 构造测试用例验证归一化后的路径比较行为：输入 `README.md` 应与 `/README.md` 判定为匹配，输入 `AI/some-image/README.md` 应与 `/AI/some-image/README.md` 判定为匹配，子目录路径不应与根目录路径混淆
3. 确认修复后 `README.en.md` 的路径检查也能通过（若该文件也会被检查）

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具在扫描 PR 变更文件时，检测到 `README.md` 的路径为 `README.md`（无前导 `/`），而工具的路径比对逻辑期望绝对路径格式 `/README.md`（带前导 `/`），路径格式不匹配导致校验失败。

### 与 PR 变更的关联
PR 仅修改了根目录的 `README.md` 和 `README.en.md`，更新了基础镜像可用 tag 列表（添加 24.03-lts-sp4/sp3/sp2、25.09 等条目）。变更内容本身没有问题，但 PR 修改的 `README.md` 被 CI appstore 预检工具扫描到，触发了待校验文件列表，从而导致路径校验失败。**失败与 PR 变更内容无关，而是 CI 工具的路径规范化逻辑问题。**

## 修复方向

### 方向 1（置信度: 高）
CI 工具 `eulerpublisher/update/container/app/update.py` 中路径比对逻辑缺少路径规范化处理。代码在比较变更文件路径与期望路径时，未对无前导 `/` 的相对路径（如 git diff 产生的 `README.md`）做归一化（即统一添加或移除前导 `/`），导致 `README.md` 与 `/README.md` 被判定为不匹配。修复方向：在路径比对逻辑中增加 `os.path.normpath` 或字符串前缀归一化处理，使两边的路径格式一致后再比较。

### 方向 2（置信度: 低）
可能 CI 工具的 appstore 发布规范检查需要一份文件清单（或白名单）来识别允许变更的文件类型，当前清单中 `README.md` 未以 `/README.md` 格式注册，导致校验失败。若方向 1 不适用，则需在 appstore 发布规范配置中将 `README.md` 以绝对路径格式注册。

## 需要进一步确认的点
- CI 工具源码 `eulerpublisher/update/container/app/update.py` 中第 273 行附近的具体路径比对逻辑实现
- 是否存在 appstore 发布规范配置文件（如白名单/路径注册表）定义了允许变更的文件路径格式
- 同一 CI 工具对英文 README（`README.en.md`）是否也做了路径校验，日志中只显示了 `README.md` 可能是工具只校验特定文件

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本修复不涉及对第三方/上游源文件的正则匹配修改。

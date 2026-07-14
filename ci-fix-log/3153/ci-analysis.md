# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 文档PR误触发appstore检查
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

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
- 失败位置: CI 工具 `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: PR 仅修改了仓库根目录的 README.md 和 README.en.md（纯文档更新），但 CI 的 appstore 发布规范检查器检测到 README.md 变更后，对其执行了应用镜像 README 路径校验，导致误报 FAILURE。仓库根目录的 README.md 是项目级别文档，并非 appstore 应用镜像的 README 文件，不应受该检查约束。

### 与 PR 变更的关联
PR 的改动（修改 README.md 和 README.en.md 中的基础镜像可用 tags 列表）触发了 CI diff 检测，使得 appstore 预检工具将根目录 README.md 纳入了检查范围。但该文件本身不属于任何 appstore 镜像制品，属于 CI 检查逻辑的误判。**此失败与 PR 代码变更的正确性无关**，文档修改内容本身没有问题。

## 修复方向

### 方向 1（置信度: 高）
CI 的 appstore 预检工具应排除仓库根目录级别的 README.md/README.en.md 文件（路径为 `/README.md` 或 `/README.en.md`），不将其纳入 appstore 镜像 README 路径校验范围。此类文件是仓库级别的项目文档，而非应用镜像的说明文档。

### 方向 2（置信度: 低）
如果 CI 检查规则要求根目录 README.md 也必须符合某种路径格式，则需要向 CI 维护者确认根目录 README.md 在 appstore 规范中的预期路径格式。但考虑到该文件位于仓库根目录且路径即为 `/README.md`，方向 1 的可能性远高于方向 2。

## 需要进一步确认的点
- 确认 CI appstore 预检工具（`eulerpublisher/update/container/app/update.py`）是否有白名单机制过滤仓库根目录文档文件，以及 `Path Error` 检查的具体逻辑（为什么 `/README.md` 作为期望路径却判定为 FAILURE）。
- 确认 PR 仅修改 README 文档时是否应该跳过 appstore 镜像规范预检（当前 CI pipeline 配置是否未区分文档类 PR 与镜像类 PR）。

## 修复验证要求
无需 code-fixer 处理。此失败为 CI 基础设施层面的误报，PR 的文档修改内容无需任何更改。应由 CI 维护者调整 appstore 预检逻辑，排除仓库根目录文档文件。

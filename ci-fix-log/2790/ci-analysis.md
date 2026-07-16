# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根级README误触发appstore校验
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore specification, eulerpublisher/update.py

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR:
There are some specification errors for releasing on appstore in this PR, please check as above.

| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检逻辑）
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档变更），未涉及任何应用镜像文件，但 CI 的 appstore 发布规范检查工具仍将 `README.md` 纳入校验范围，并对其执行了路径校验，导致误报 `[Path Error]`。该文件位于仓库根路径 `/README.md`，本身不匹配任何应用镜像的路径模式，也无需通过 appstore 发布规范校验。

### 与 PR 变更的关联
PR #2790 的改动完全限定在文档层面：修改了 `README.md` 和 `README.en.md` 中"可用镜像 Tags"列表，新增了 `24.03-lts-sp3`、`25.09` 条目，并修正了 `24.03-lts-sp2` 的锚链接 URL（从错误的 `SP1` 改为正确的 `SP2`）。这些变更不会触发任何构建、测试或应用的打包发布流程。CI 失败是 appstore 检查工具在扫描 PR diff 时，将一个不应被校验的根级文档文件错误地纳入了路径规范检查，属于 CI 工具逻辑问题，与 PR 代码变更内容无关。

## 修复方向

### 方向 1（置信度: 高）
CI 检查工具（`eulerpublisher/update/container/app/update.py` 第 273 行附近的 appstore 规范校验逻辑）应增加根级 README.md 文件的豁免规则。当 diff 中仅包含仓库根级文档文件（如 `/README.md`、`/README.en.md`）且无任何应用镜像目录下的文件变更时，跳过 appstore 发布规范校验。或者更通用地，将检查范围限定在应用镜像目录（`Bigdata/`、`AI/`、`Database/` 等）内的文件，排除根级纯文档文件。

### 方向 2（置信度: 中）
对于当前 PR #2790，可考虑由 CI 管理员手动 bypass 该 appstore 检查步骤，因为变更仅涉及根级 README 文档，不存在任何应用镜像发布、构建或测试层面的风险。此方案为应急绕过，长期仍需方向 1 的检查工具逻辑修复。

## 需要进一步确认的点
- `eulerpublisher/update/container/app/update.py` 第 273 行的具体校验逻辑：它通过什么规则判断哪些 diff 文件需要被 appstore 路径校验，以及为什么根级 README.md 没有被豁免。
- 该 CI Job 是否有配置文件（如 Jenkinsfile 或 CI 编排脚本）定义了 `Difference` 计算逻辑或文件过滤规则，确认是否可以在 Job 层面过滤根级文档文件。

## 修复验证要求
无需验证——本失败为 CI 基础设施问题，PR 代码本身无需修改。

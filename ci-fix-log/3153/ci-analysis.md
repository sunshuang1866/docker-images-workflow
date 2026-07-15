# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: 文档MR未跳过行规检查
- 新模式症状关键词: Path Error, expected path, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: Jenkins x86-64 下游构建 job，`eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检（PR 触发的自动化校验）对根目录下被修改的 `README.md` 报告路径错误：期望路径为 `/README.md`。PR 仅包含两个根级文档文件（`README.md`、`README.en.md`）的 Tags 列表更新，属于纯文档修改，不涉及任何应用镜像 Dockerfile 或元数据文件变动，但 CI 的 appstore 规范检查未能正确识别文档-only 变更并跳过校验。

### 与 PR 变更的关联
PR #3153 仅修改了 `README.md` 和 `README.en.md` 中第 2 节"可用镜像的 Tags"列表（将 "24.03-lts-sp2, 24.03, latest" 更新为 "24.03-lts-sp4, 24.03, latest"，并新增 `24.03-lts-sp3`、`25.09` 条目）。这些变更为纯文档更新，与任何构建逻辑、Dockerfile、CI 配置均无关。CI appstore 规范检查将根目录 `README.md` 识别为不符合发布规范的路径，但该检查对文档-only PR 本身不适用。

## 修复方向

### 方向 1（置信度: 低）
CI appstore 规范检查工具应在识别到 PR 仅包含根级文档文件变更时自动跳过验证，或放宽根级 `README.md` 的路径约束。若该行为是 CI 工具 `eulerpublisher` 的预期行为，则需在 CI 流水线配置中将 appstore 规范检查限制为仅对非文档目录（`Base/`、`Bigdata/`、`AI/`、`Storage/`、`Database/`、`Cloud/`、`HPC/`、`Distroless/`、`Others/`）下的文件生效。

### 方向 2（置信度: 低）
若 `[Path Error] The expected path should be /README.md` 的实际含义是 CI 工具在解析 `README.md` 内容时，要求内部引用的路径使用带前导 `/` 的绝对路径格式（而非 `README.md` 本身的位置错误），则需检查 PR diff 中新增的链接 URL 格式是否符合 appstore 规范。但根据当前日志证据，此可能性较低。

## 需要进一步确认的点
1. CI 日志中上游触发信息显示 "PR 3184 [sunshuang1866:fix/3153 -> master]"，与上下文 PR 编号 #3153 不一致，需确认是否为同一 PR 的不同流水线实例。
2. 当前日志仅来自 x86-64 下游 job，需确认是否有其他架构的并行构建 job 同样失败，以及各架构的失败模式是否一致。
3. 需查阅 `eulerpublisher/update/container/app/update.py` 中 `[Path Error]` 的判断逻辑，确认其具体校验规则及为何对根级 `README.md` 报错。
4. 需确认 appstore 发布规范检查是否为 CI 流水线的必经步骤——若是且预期文档 PR 不应触发，则需修改流水线配置；若该检查本应可通过，则需排查是否有其他隐藏原因（如 runner 文件系统权限、git 克隆路径异常等）导致工具误判。

## 修复验证要求
无需 code-fixer 操作——该失败属于 CI 基础设施/流水线配置问题（infra-error），与 PR 的代码/文档变更内容无关。建议由 CI 维护者排查 `eulerpublisher` 工具的 appstore 路径校验逻辑，或调整流水线触发条件以跳过文档-only MR。

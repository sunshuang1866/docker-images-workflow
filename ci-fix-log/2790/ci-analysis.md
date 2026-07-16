# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（宽松匹配 — 机制同为 appstore 发布规范路径校验失败，但触发场景不同）
- 新模式标题: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具对 PR 变更文件进行路径校验，仓库根目录下的 `README.md` 不被视为任何应用镜像（`{category}/{image}/{version}/{os-version}/`）路径下的有效文件，路径校验不通过。

### 与 PR 变更的关联
**直接关联**。PR 仅修改了两个文档文件：
- `README.md` — 更新支持的 Tags 列表（将 latest 从 `24.03-lts-sp2` 更新到 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）
- `README.en.md` — 同上英文版

CI 对 `README.md` 进行 appstore 发布规范路径校验，由于该文件位于仓库根目录而非任何应用镜像目录下，校验失败。`README.en.md` 未出现在 `Difference` 列表中，说明 checker 对其进行了过滤，但 `README.md` 被纳入检查范围。

核心矛盾：这是一个**纯文档 PR**（不涉及任何 Dockerfile、meta.yml、image-list.yml 等应用镜像构建文件），而 CI 的 appstore 发布规范检查器设计预期处理的是镜像构建 PR，将根级文档文件错误地纳入检查范围导致误报。

## 修复方向

### 方向 1（置信度: 中）
**无需修复代码**。PR 的改动完全合法（仅更新 README 文档中已变更的 openEuler 版本及 Tag 链接），CI 的 appstore 路径校验对此类纯文档 PR 属于误报。建议直接由维护者通过合并，或通过调整 CI pipeline 配置使文档类变更跳过 appstore 规范校验。

由于 PR 仅涉及仓库根级 README 文档更新，可通过 PR 标签或 CI 触发条件区分文档 PR 与镜像构建 PR。

### 方向 2（置信度: 低）
若 CI 确实要求所有 PR 通过 appstore 校验且无法跳过，则 `README.md` 的路径变更可能需要在 appstore 的校验元数据中注册为合法路径（如在 `image-list.yml` 或类似配置中添加根级 `README.md` 的豁免条目）。但从仓库规范和 PR 性质看，此方向不合逻辑。

## 需要进一步确认的点
1. **CI pipeline 是否有条件分支**：当前 CI 是否对所有 PR 无条件触发 appstore 校验，还是可基于 PR 标签（如 `documentation`、`docs-only`）跳过该步骤？需要查阅 CI 流水线配置（Jenkinsfile 或 `.github/workflows/`）。
2. **update.py 的路径过滤逻辑**：`README.en.md` 同样被修改却未出现在 `Difference` 列表中，而 `README.md` 出现。需确认 `update.py` 中文件过滤的条件是什么（文件名模式、扩展名还是路径前缀），以理解为何仅 `README.md` 被选中检查。
3. **该检查是否为阻塞项**：appstore 路径校验失败是否硬性阻止 PR 合并，还是仅为非阻塞性通知（notify）？从日志 `Build step 'Execute shell' marked build as failure` 判断当前为阻塞性失败。
4. **证据充分性存疑**：日志中的错误信息 `[Path Error] The expected path should be /README.md` 的语义存在歧义：「`/README.md` 就是不合法路径」还是「文件应位于 `/README.md` 但实际路径不匹配」？由于 `README.md` 实际就位于仓库根目录（即 `/README.md`），若为后者则说明 checker 存在路径归一化 bug（如对比时一方带 `/` 前缀另一方不带）。需要查看 `update.py` 源码确认校验逻辑。

## 修复验证要求
（不适用 — 本报告推荐方向为 CI pipeline 调整，不涉及代码修复或正则 patch）

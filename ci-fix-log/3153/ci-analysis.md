# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, expected path should be, README.md, update.py, appstore

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
- 失败原因: CI 的 appstore 发布规范预检工具对 PR 中变更的 `README.md`（仓库根目录文件）进行了路径校验，但校验逻辑判定其不符合预期路径格式 `/README.md`。实际上 `README.md` 就位于仓库根目录，路径等价，此报错属于 CI 工具路径字符串比对逻辑缺陷（缺少相对路径到绝对路径的归一化处理）。

### 与 PR 变更的关联
PR 仅修改了两个根目录文档文件：
- `README.md` —— 更新可用基础镜像 tags 列表
- `README.en.md` —— 英文版同步更新

这两个文件均为纯文档维护性变更，不涉及任何 Dockerfile、meta.yml、image-info.yml 等应用镜像构建文件。PR 本身不应触发 appstore 发布规范检查。CI 工具没有正确识别 PR 的变更范围（仅文档），错误地将 `README.md` 纳入 appstore 路径校验流程并产生误报。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施/工具问题，PR 代码无需修改。该 CI 预检工具 `eulerpublisher/update/container/app/update.py` 的路径校验逻辑在处理纯文档 PR（根级别 README 变更）时存在误报。需要 CI 维护方调整校验规则，将仅变更根目录文档文件的 PR 排除在 appstore 发布规范检查之外，或修复路径比对中的归一化缺陷。

### 方向 2（置信度: 低）
若 CI 工具短期内无法调整，可尝试用 `git mv` 替代直接修改 `README.md`，观察是否能绕过路径检测逻辑。但此方向属于 workaround，且可能性较低，不推荐。

## 需要进一步确认的点
1. **CI 工具源码**：需查阅 `eulerpublisher/update/container/app/update.py:273` 及其 `Difference` 变更筛选逻辑（同文件 `line:356`），确认路径比对的具体实现方式，以判断是归一化缺陷还是规则覆盖不全。
2. **同类历史案例**：PR #2512 中存在类似的 `.claude/agents/README.md` 路径校验失败记录（见模式11），可参考其最终处置方式——是修改了文件路径还是 CI 放行了该检查。
3. **PR 触发机制**：确认该 CI job 的触发条件是否包含对文件变更范围的过滤（例如仅当变更涉及 `Base/`、`AI/`、`Bigdata/` 等应用镜像子目录时才运行 appstore 检查），当前是否缺少此过滤条件。

## 修复验证要求
本报告判定为 infra-error，无需 code-fixer 提交代码修复。若后续确认需要修改 `eulerpublisher` 工具代码，则需由 CI 平台维护团队进行验证。

# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README路径校验误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py`:273（CI 工具 appstore 发布规范校验步骤）
- 失败原因: CI 的 appstore 发布规范检查对仓库根目录下的 `README.md` 文件进行了路径校验，报告期望路径应为 `/README.md`，校验失败。PR 仅修改了根目录的 `README.md` 和 `README.en.md`，是对基础镜像 Tags 列表的纯文档更新，该文件本身位于根目录（即 `/README.md`），路径实际正确，但 CI 工具对其路径解析或校验规则可能与预期不符。

### 与 PR 变更的关联
PR 变更仅涉及 `README.md` 和 `README.en.md` 中基础镜像 Tags 列表的内容更新（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目，修正了原 `latest` 标签指向的 URL 版本）。变更本身不涉及任何 Dockerfile、构建脚本或代码逻辑。CI 的 appstore 发布规范校验（`update.py`）在此次运行时将仓库根目录的 `README.md` 也纳入了 appstore 发布规范检查，导致路径校验失败。该检查可能仅适用于镜像目录内的元数据文件，不应作用于根级项目说明文档。**注意**：提供的 CI 日志实际来自 PR #3184（分支 `fix/3153`），该日志可能反映的是 #3153 原始问题的复现或修复过程中的中间状态。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 校验工具 `eulerpublisher/update/container/app/update.py` 在扫描 PR diff 中的变更文件时，未正确排除仓库根目录级别的通用文档（如 `/README.md`），导致路径校验逻辑对这类文件也执行了 image 目录结构的路径期望检查。应在 CI 工具的 diff 文件过滤逻辑中增加对仓库根目录文件的白名单/跳过规则。

### 方向 2（置信度: 低）
CI 工具在解析 git diff 输出中的文件路径时（如 `b/README.md`），可能存在路径规范化问题——提取出的路径缺少前导 `/`，与期望的 `/README.md` 格式不匹配，导致字符串比较失败。

## 需要进一步确认的点
1. 需要确认 CI 日志对应的 PR #3184 与该待分析 PR #3153 的变更是否完全一致（#3184 分支名为 `fix/3153`，可能是同一 diff 的重建 PR，也可能引入了额外修改）。
2. 需要查看 `eulerpublisher/update/container/app/update.py` 的源码（特别是 line 273 附近的路径校验逻辑），确认 `[Path Error] The expected path should be /README.md` 的具体触发条件和路径比较方式。
3. 需确认 `README.en.md` 是否同样经过了该校验流程——日志中仅报告了 `README.md` 的问题（在 `Difference` 日志中也只列出了 `README.md`），是否有其他逻辑使得 `README.en.md` 被跳过了。
4. 证据不足以完全排除 CI 工具 bug 的可能——如果同一个 PR 在重新触发 CI 后通过，则可确认基础设施问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败与外部源文件 patch 无关，不涉及正则表达式修改。如修复方向选择修改 CI 工具源码 `eulerpublisher/update/container/app/update.py`，则 code-fixer 在修改后需重新触发 CI 验证根目录 README 变更不再触发 Path Error。

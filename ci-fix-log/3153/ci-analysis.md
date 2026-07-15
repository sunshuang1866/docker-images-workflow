# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-INFO: Difference: [
    "README.md"
]
2026-07-14 11:28:17,839-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 工具 `eulerpublisher` 的 appstore 发布规范预检对仓库根目录的 `README.md` 产生了路径校验误判——README.md 实际位于 `/README.md`（仓库根目录），但 CI 检查工具将其判为路径不合法。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅修改了 `README.md` 和 `README.en.md` 中基础镜像 Tags 的文档内容（新增 `24.03-lts-sp4`、`24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 标签，理顺排序），未改动任何代码、Dockerfile、构建逻辑或文件路径。CI 的 `eulerpublisher` appstore 预检工具对根目录存在的 `README.md` 路径校验出现误报，属于 CI 工具层面的问题。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施问题，无需修改 PR 代码。`eulerpublisher` 工具在 appstore 发布规范预检中对仓库根级 `README.md` 的路径判断逻辑存在缺陷（可能因 git diff 输出的 `a/README.md` 路径格式与工具内部预期的 `/README.md` 格式不匹配导致）。需由 CI 工具维护者排查 `eulerpublisher/update/container/app/update.py` 中路径校验逻辑，或为根级非镜像文件（如 README.md）添加豁免规则。

### 方向 2（置信度: 低）
若 README.md 的变更确实不应出现在 appstore 预检范围内，可能需要在 CI 触发条件中过滤掉纯文档类文件变更，避免对 README.md 执行不必要的 appstore 规范检查。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行附近的路径校验逻辑，确认其是如何从 git diff 获取文件路径并进行格式比对的。
2. CI 的 appstore 预检阶段是否应该对仓库根级 README.md 执行路径规范检查——这从设计上似乎不合理（README.md 不是应用镜像的元数据文件）。
3. 该 CI 预检失败的触发条件：是否只要 PR diff 包含任何非镜像目录的文件，都会进入 appstore 路径校验流程并报错。

## 修复验证要求
不适用（infra-error，无需 code-fixer 修改代码）。

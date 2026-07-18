# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11（YAML / 元数据文件错误——应用商店路径校验）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的应用商店（appstore）发布规范校验工具 `eulerpublisher` 对所有 PR 强制执行路径校验，要求变更文件遵循 `{category}/{image}/{version}/{os-version}/` 的镜像目录层级结构。本 PR 仅修改了仓库根目录的两个 README 文档（`README.md`、`README.en.md`），不包含任何 Docker 镜像构建文件，根级 README 路径不符合应用商店镜像路径规范，导致校验失败。

### 与 PR 变更的关联
PR 的改动仅涉及更新 README 中基础镜像的可用 Tags 列表（文档内容更新），不增删任何 Dockerfile 或镜像元数据。CI 失败由 PR 触发（PR 触发 CI 流水线运行），但失败根因是 CI 流程配置问题——应用商店路径校验对非镜像类 PR 无豁免机制。PR 的代码变更本身无任何错误。

## 修复方向

### 方向 1（置信度: 高）
CI 的应用商店校验步骤应增加 PR 类型判断，对于仅修改仓库根级文档（非镜像目录内文件）的 PR 豁免路径校验。这需要 CI 流水线配置层面的调整（例如在 trigger job 或 `eulerpublisher` 调用脚本中添加文件变更范围检测逻辑），而非本 PR 代码层的修改。

### 方向 2（置信度: 中）
如果 CI 流水线短时间内无法调整，可考虑将文档更新 PR 以其他方式合入（如通过具有绕过权限的账号直接提交，或走不触发 appstore 检查的分支策略）。

## 需要进一步确认的点
- CI 流水线配置（Jenkins job 定义或调用 `eulerpublisher` 的 shell 脚本）中应用商店校验步骤的触发条件，确认是否有现成的"仅镜像目录变更"判定逻辑。
- 该仓库的贡献流程是否区分"镜像 PR"和"文档 PR"，以及文档类变更是否有单独的 CI 通道或豁免规则。

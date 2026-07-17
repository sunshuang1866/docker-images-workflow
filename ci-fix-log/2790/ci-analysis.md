# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455 update.py[line:356]-INFO: Difference: [
    "README.md"
]
2026-07-14 15:28:07,685 update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: 仓库根目录 `README.md`
- 失败原因: CI 的 appstore 发布规范检查工具（`eulerpublisher/update/container/app/update.py:273`）在 PR 变更文件扫描阶段检测到根目录 `README.md` 被修改，对其执行了 appstore 镜像 README 路径校验。根目录的 `README.md` 是项目级文档，不满足 appstore 对镜像 README 的路径格式要求（期望位于应用镜像目录内，如 `{category}/{image}/{version}/README.md`），因此被标记为 FAILURE。

### 与 PR 变更的关联
本次 PR 仅修改了根目录下的 `README.md` 和 `README.en.md`（更新支持的镜像 Tags 列表：新增 25.09，修正 24.03-lts-sp2/sp3 条目和链接），为纯文档更新。CI 的 appstore 检查步骤会扫描所有变更文件并进行路径校验，根目录 README.md 被纳入检查范围后因不满足 appstore 镜像目录路径规范而失败。**失败由 PR 变更直接触发，但根本原因是 CI 检查未区分仓库级文档与应用镜像级文件。**

## 修复方向

### 方向 1（置信度: 高）
在 CI appstore 检查工具（`update.py`）中增加根目录文件排除逻辑。当变更文件路径不含场景分类目录前缀（如 `Bigdata/`、`AI/`、`Cloud/`、`Database/`、`HPC/`、`Storage/`、`Others/`、`Distroless/`、`Base/`）时，跳过 appstore 路径规范校验，或将校验仅应用于应用镜像最小目录单元内的文件。

### 方向 2（置信度: 中）
若 CI 工具逻辑无法直接修改，可将根目录 README.md 的修改拆分为独立 PR，避免与 appstore 镜像变更混合提交，从而规避 appstore 检查步骤。

## 需要进一步确认的点
- `update.py` 的 appstore 路径校验逻辑中对文件过滤的具体实现（现有排除规则是什么）
- 该 CI 检查是否对所有涉及根目录 README.md 的 PR 均会失败（是否为系统性问题）

## 修复验证要求
（本次修复涉及 CI 工具配置/排除规则调整，不涉及正则 patch 外部源文件，无需额外验证）

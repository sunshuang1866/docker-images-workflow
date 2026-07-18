# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI工具路径比较缺陷
- 新模式症状关键词: Path Error, expected path should be, README.md, appstore specification, eulerpublisher/update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: CI 工具 `update.py` 对 PR diff 中检测到的 `README.md` 文件执行 appstore 发布规范路径校验时，将相对路径 `README.md` 与期望的绝对路径格式 `/README.md` 进行比较，由于路径格式不匹配（有无前导 `/`）导致校验失败。PR 本身仅修改了仓库根目录下的 `README.md` 和 `README.en.md` 文档文件，更新了可用基础镜像的 Tags 列表，这些文件路径本身是合法合规的。

### 与 PR 变更的关联
PR 变更与 CI 失败**无因果关系**。本次 PR 仅为文档更新（在 `README.md` 和 `README.en.md` 中增删基础镜像 tag 条目），不涉及任何 Dockerfile、元数据文件（`meta.yml`、`image-info.yml`）、构建脚本或应用镜像的变更。CI 失败源于 appstore 校验工具对根目录 `README.md` 的路径格式比对逻辑缺陷（相对路径 vs 绝对路径），属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 中）
CI `update.py` 工具在路径比较时存在格式不一致问题：`Difference` 输出的文件路径为 `README.md`（无前导 `/`），而校验器期望的路径格式为 `/README.md`（有前导 `/`）。需在 `eulerpublisher/update/container/app/update.py` 中统一路径归一化逻辑，确保比较双方使用一致的路径格式（如均使用前导 `/` 或均去掉前导 `/` 后再比较）。

### 方向 2（置信度: 低）
可能是 CI appstore 校验流程设计问题：对于纯文档类 PR（仅修改仓库根目录 README 文件、不含任何应用镜像 Dockerfile 或元数据变更），appstore 发布规范校验本身不应被触发。可在 CI 编排层增加前置过滤——当 diff 仅包含根目录 `README.md`/`README.en.md` 等文档文件时，跳过 appstore 规范检查。

## 需要进一步确认的点
1. 需要查看 `eulerpublisher/update/container/app/update.py:273` 及其上下文代码，确认路径比较的具体实现逻辑（是否为简单的字符串相等比较）。
2. 需要确认该 CI appstore 校验步骤是否为本次 PR 才触发的（即该步骤近期是否有变更），以排除"CI 工具近期引入回归"的可能性。
3. 日志中 `Difference: ["README.md"]` 仅检测到 `README.md`，未检测到 `README.en.md`。需确认 CI diff 逻辑是否遗漏了部分文件，或是否仅选取了变更文件中的第一个。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher` 工具（`update.py`）的路径比较逻辑，code-fixer 必须在修复前：
1. 从 eulerpublisher 仓库获取 `update.py` 源文件，确认路径比较代码的实际实现方式。
2. 验证修复后的路径归一化逻辑对不同输入格式（`README.md`、`./README.md`、`/README.md`）均能正确通过校验。

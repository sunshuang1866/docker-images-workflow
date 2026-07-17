# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根目录文档误触发应用校验
- 新模式症状关键词: Path Error, The expected path should be, update.py, appstore, README.md

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
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI 的 appstore 发布规范预检工具 `update.py` 对 PR 中变更的所有文件执行路径校验，根目录 `README.md` 不是应用镜像文件，不属于 appstore 发布规范的适用范围，但 CI 工具仍对其施加了路径格式检查，导致校验失败。PR 仅修改了根目录的 `README.md` 和 `README.en.md`（文档更新），无任何应用镜像 Dockerfile 变更。

### 与 PR 变更的关联
PR 的改动（更新 README 中的基础镜像 Tag 列表）本身**不会**直接触发该失败——根目录 README 的内容和路径均正确。失败的原因是 CI 工具 `update.py` 将 appstore 发布路径校验逻辑错误地应用到根目录非应用文件上。这是一个 CI 工具设计缺陷：只要 PR 中包含了 `README.md` 的变更，无论变更内容是什么，该检查都会失败。

## 修复方向

### 方向 1（置信度: 中）
CI 工具 `update.py` 需在路径校验前增加过滤逻辑，排除根目录级别的通用文件（如 `/README.md`、`/README.en.md`、`/CONTRIBUTING.md` 等），仅对应用镜像目录（如 `Bigdata/`、`AI/`、`Database/`、`Cloud/`、`HPC/`、`Storage/`、`Distroless/`、`Others/` 及其子目录）下的文件执行 appstore 路径格式校验。修复范围为 `eulerpublisher` 仓库中的 `update.py`，非本 PR 仓库。

### 方向 2（置信度: 低）
若 CI 工具不可修改，可考虑在 PR 中将与 README.md 无关的其他必要应用镜像变更一并提交，使 CI 检测到的差异列表中仅包含符合 appstore 路径规范的文件。但 PR #3153 本身就是一个纯文档更新，此方向不合理。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 在第 273 行附近的具体校验逻辑是什么，它是根据什么规则判定 `README.md` 的路径不符合预期的（"expected path should be /README.md" 中 `/README.md` 在仓库中真实存在，为何仍判定不通过）
2. `update.py` 的设计意图是否为"对所有变更文件进行路径校验"还是"仅对应用镜像目录下的文件进行校验"——后者才是正确行为
3. 同类纯文档 PR（仅修改根目录 README 或非应用镜像文件）是否均有此问题，如果是，则为 CI 工具已知缺陷，应统一修复而非逐 PR 绕过

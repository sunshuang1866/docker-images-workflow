# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI路径格式校验偏差
- 新模式症状关键词: Path Error, expected path, README.md, appstore, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171-...-INFO: Difference: [
    "README.md"
]
2026-07-16 20:34:43,051-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 编排工具内）
- 失败原因: CI appstore 发布规范预检工具在扫描 PR 变更文件时，将 `README.md`（无前导 `/`）与预期路径 `/README.md`（带前导 `/`）进行了逐字匹配，因路径格式偏差（缺少前导 `/`）判定为 FAILURE。该校验发生在构建流程之前，没有执行任何实际的 Docker 镜像构建。

### 与 PR 变更的关联
**与 PR 变更无关（infra-error）**。PR 仅修改了 `README.md` 和 `README.en.md` 两个文档文件（更新可用基础镜像 tags 列表），没有任何 Dockerfile、meta.yml、image-list.yml 或应用镜像相关文件的变更。CI 失败是 eulerpublisher 工具在 appstore 发布规范预检阶段将仓库根目录 README 文件的路径格式（无前导 `/`）误判为不符合规范所致。该 PR 原本就不属于应用镜像上架范畴，不应受 appstore 规范的约束。

## 修复方向

### 方向 1（置信度: 高）
**eulerpublisher CI 工具侧修复**：在 `eulerpublisher/update/container/app/update.py` 中，对路径比对逻辑增加路径标准化处理——在比较前为无前导 `/` 的相对路径补充 `/`，或改为使用 `os.path.normpath` 等价比较，消除格式偏差导致的误判。此修复不在本仓库代码范围内，需由 CI 基础设施团队在 eulerpublisher 仓库中实施。

### 方向 2（置信度: 低）
**PR 侧 workaround**：如果 CI 工具短期内无法修复，可考虑在 appstore 校验逻辑中增加对仓库根目录文档（`README.md`、`README.en.md`）的排除规则，使纯文档 PR 不被 appstore 预检阻塞。但这同样是 CI 工具侧的改动。

## 需要进一步确认的点
1. eulerpublisher 的路径比对逻辑源码（`update.py:273` 附近的 `check` 函数），确认路径拼接/标准化是否确实缺少 `os.path.join` 或 `startswith('/')` 处理。
2. 该 appstore 预检是否对仓库根目录 README 变更**本就不应触发**——如果是，说明是触发条件过于宽泛的设计缺陷；如果不是，则需确认预期的路径格式规范。
3. 同类 PR（纯文档修改）之前是否也触发了同样的 CI 失败，用于复现和验证该问题的普遍性。

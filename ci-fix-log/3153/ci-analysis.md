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
2026-07-14 11:28:17,839- update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 验证工具，非 PR 代码）
- 失败原因: CI appstore 发布规范预检工具（eulerpublisher）将仓库根目录下的 `README.md` 纳入 appstore 路径校验范围，但 `README.md` 作为仓库级文档文件，不属于任何应用镜像条目，其实际路径 `/README.md` 已与"期望路径 `/README.md`"一致，仍被判定为 FAILURE。结合 `Difference` 日志中显示 `"README.md"`（无前导 `/`）而期望为 `/README.md`（有前导 `/`），高概率为 CI 工具的路径字符串比较未做归一化处理，或该工具未将根层级文档文件排除在 appstore 校验范围之外。

### 与 PR 变更的关联
- PR 变更仅涉及根目录下的 `README.md` 和 `README.en.md` 两个文档文件，内容为更新可用基础镜像标签列表（将 `latest` 从 24.03-lts-sp2 提升到 24.03-lts-sp4，新增 24.03-lts-sp3、25.09 等条目）。
- **PR 内容变更本身是正确的文档更新，不包含任何应用镜像 Dockerfile、meta.yml 等应受 appstore 校验的文件。**
- CI 预检工具在扫描 PR diff 时错误地将根层级 `README.md` 纳入 appstore 发布规范检查，导致误报。该失败与 PR 改动内容无关，属于 CI 工具逻辑缺陷。

## 修复方向

### 方向 1（置信度: 中）
CI 编排工具 `eulerpublisher` 的 appstore 路径校验逻辑存在缺陷：未将仓库根目录下的文档文件（`/README.md`、`/README.en.md` 等）排除在应用镜像路径校验范围之外。需要修改 `update.py` 中的 diff 分析逻辑，在遍历被修改文件时跳过根层级文档文件（无类别目录前缀的文件），或对根层级 README 做路径归一化处理（统一加前导 `/` 后再比较）。

### 方向 2（置信度: 低）
如果 CI 工具的设计意图是要求所有被修改的 README.md 都必须符合 appstore 发布规范格式，则需要在根层级 README.md 中补充符合 appstore 规范的元数据（如 Copyright 头、SPDX 标识等）。但这种设计不合理——仓库级 README 不应受 appstore 规范约束。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中第 273 行前后的路径校验逻辑具体实现——确认是字符串比较缺失归一化还是未过滤非应用镜像文件。
2. 确认 CI 的历史行为：是否之前的文档类 PR（仅修改根层级 README）也会触发此检查并失败？如果之前通过而现在失败，说明 CI 工具近期有变更。
3. 日志中 `Difference` 仅列出 `README.md` 而未列出同样被修改的 `README.en.md`——需确认 diff 分析逻辑是否有遗漏或特殊处理。

## 修复验证要求
（不适用——此失败为 infra-error，由 CI 工具逻辑缺陷导致，不涉及对 PR 代码的修改。）

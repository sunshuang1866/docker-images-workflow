# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径检查误报
- 新模式症状关键词: Path Error, The expected path should be, README.md, appstore, 根目录文档

## 根因分析

### 直接错误
```
2026-07-16 20:34:43,051-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 预检工具 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具检测到 PR 变更了 `README.md`（根目录文档），在路径校验时认为 git diff 返回的路径格式 `README.md`（缺少前导 `/`）与期望格式 `/README.md` 不匹配。实际文件路径正确，该报错为 CI 工具路径归一化处理的误报。

### 与 PR 变更的关联
PR #3153 **仅修改了两个根目录下的 README 文档文件**（`README.md` 和 `README.en.md`），更新了基础镜像可用 tags 列表（新增 24.03-lts-sp4/sp3、25.09、24.03-lts-sp2 条目并调整 sort 顺序）。PR 不包含任何 Dockerfile、构建脚本、meta.yml、image-list.yml 或应用镜像目录下文件的变更。CI 失败是由预检工具对非应用镜像文件的过度校验导致，与 PR 的实际文档内容变更**无因果关系**。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具对纯文档类文件（根目录 `README.md`、`README.en.md`）未做豁免，路径归一化处理缺少前导 `/` 补全逻辑。该问题属于 CI 基础设施工具行为，与 PR 代码变更无关。建议由 CI 维护团队：
- 在预检工具中为根目录文档文件（非应用镜像目录下的文件）添加豁免规则；或
- 对 git diff 输出的路径做归一化处理（统一补全前导 `/`）

## 需要进一步确认的点
- 确认该 `[Path Error]` 是路径前缀归一化缺失导致，还是预检工具对根目录文件有其他隐性约束（如要求 README 变更仅可在特定子目录下）
- 确认是否有下游架构构建 job（如 aarch64）的日志，排除该 job 中是否存在其他独立的构建失败
- 确认 CI 预检工具对纯文档 PR 的豁免策略是否存在已知缺陷

## 修复验证要求
（无。该失败属于 infra-error，不涉及 Dockerfile 修改或源码 patch。）

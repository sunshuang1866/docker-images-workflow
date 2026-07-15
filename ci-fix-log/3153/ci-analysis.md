# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式（弱关联模式11）
- 新模式标题: 文档变更触发appstore检查
- 新模式症状关键词: Path Error, expected path, appstore, README.md, update.py, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: CI 工具 `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检流程将根目录 `README.md`（无前导 `/` 的路径表示）与期望格式 `/README.md`（带前导 `/`）进行对比，因路径格式不一致导致 Path Error；此外，该 PR 为纯文档变更（仅修改 README.md / README.en.md 中的基础镜像 tag 列表），并不涉及任何应用镜像的新增或修改，不应触发 appstore 发布规范检查

### 与 PR 变更的关联
PR #3153 改动仅涉及文件：
- `README.md`：更新基础镜像 tag 列表（`24.03-lts-sp2` 不再作为 latest，新增 `24.03-lts-sp4` / `24.03-lts-sp3` / `25.09` / `24.03-lts-sp2`）
- `README.en.md`：同上，英文版同步更新

以上为纯文档维护性变更，不涉及 Dockerfile、meta.yml、image-info.yml 等构建或元数据文件。CI 流水线中的 eulerpublisher appstore 预检工具（`update.py`）未排除根级文档文件的检查，导致此 PR 被错误拦截。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 规范检查工具（`eulerpublisher/update/container/app/update.py`）应跳过根级文档文件（`/README.md`、`/README.en.md`）的路径校验，或对路径做标准化处理（统一添加/去除前导 `/`）后再比较。此修复在 CI 工具侧进行，本 PR 代码无需修改。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 第 273 行附近的具体路径校验逻辑——对比路径时是否对前导 `/` 做了归一化处理
2. 确认 CI 触发信息中的 PR #3184（分支 `fix/3153`）与上下文中的 PR #3153 是否对应同一变更，是否存在 PR 编号混淆
3. 确认 appstore 预检工具是否有配置项可排除根级文档文件（非应用镜像相关文件）的检查范围
4. 若 CI 日志来自 trigger/编排层 job（当前日志末尾为 `Finished: FAILURE` 且不含 Docker build 步骤），需进一步获取下游 x86-64 架构构建 job 的完整日志，以排除是否存在其他未暴露的并行失败

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败为 CI 工具配置问题，不涉及外部源文件的正则匹配修改。

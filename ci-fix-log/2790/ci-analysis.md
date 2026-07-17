# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 根README触发APP校验
- 新模式症状关键词: appstore, Path Error, expected path, specification errors, update.py, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-/home/jenkins/agent-working-dir/workspace/multiarch/****/x86-64/****-docker-images/eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI 预检工具）
- 失败原因: CI appstore 发布规范预检工具对 PR 中变更的根目录 `README.md` 进行了校验，判定其不符合 appstore 镜像 README 的路径规范要求，报 `[Path Error] The expected path should be /README.md`。

### 与 PR 变更的关联

**直接关联。** PR #2790 仅修改了两个文件：
- `README.md`（根目录，中文 README）
- `README.en.md`（根目录，英文 README）

变更内容为更新基础镜像 Tags 列表（新增 24.03-lts-sp3、25.09 等条目，调整 latest 标签指向）。这些是仓库级文档更新，**不涉及任何应用镜像的 Dockerfile、meta.yml 或 image-info.yml**。

CI 的 appstore 发布预检工具（`update.py`）在扫描 PR 变更文件时，将根目录 `README.md` 纳入了 appstore 规范检查。由于根目录 README.md 是仓库整体说明文档，其格式和内容不符合 appstore 对镜像级 README 的规范要求（appstore 期望 README 位于 `{category}/{image}/{version}/README.md` 路径下且具有特定内容结构），因此校验失败。

注意：CI diff 日志 `Difference: ["README.md"]` 仅列出了 `README.md`，未列出 `README.en.md`，说明预检工具可能只对特定文件名模式进行校验。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 预检工具应将仓库根目录级别的 README.md（非镜像目录下的 README）排除在校验范围之外。根目录 README 是项目整体文档，不应受 appstore 镜像发布规范约束。此方向需要修改 CI 编排工具 `eulerpublisher` 的 `update.py` 中文件过滤逻辑，在扫描变更文件列表时跳过仓库根目录下的 README.md / README.en.md。

### 方向 2（置信度: 低）
如果根目录 README.md 确实需要纳入 appstore 规范校验，则需要按其规范添加必要的元数据字段或格式头（如 Copyright/SPDX 声明），使其通过预检。但考虑到 `README.md` 是仓库主文档且 PR 变更均属纯内容更新（非新增镜像），此方向实操意义有限。

## 需要进一步确认的点
1. CI 预检工具 `update.py` 中校验变更文件的逻辑：为何将根目录 `README.md` 纳入 appstore 检查范围，具体筛选条件是什么。
2. 历史案例模式11（PR #2512）中有类似的 `.claude/README.md` 路径校验失败记录，需确认当前 CI 预检工具的路径校验规则是否已有针对性的修复，以及该修复是否遗漏了根目录场景。
3. `README.en.md` 未出现在 `Difference` 列表中的原因——是校验工具仅扫描 `README.md` 文件名，还是 `README.en.md` 的 diff 被其他逻辑过滤。

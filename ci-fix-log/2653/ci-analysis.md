# CI 失败分析报告

## 基本信息
- PR: #2653 — 【自动升级】cmaq容器镜像升级至5.5.2Oct2024版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Git分支名构造错误
- 新模式症状关键词: `fatal: Remote branch`, `not found in upstream origin`, `git clone`, `exit code: 128`, `CMAQv`

## 根因分析

### 直接错误
```
#11 [builder 5/5] RUN git clone -b CMAQv5.5.2Oct2024_2Oct2024 --depth 1 https://github.com/USEPA/CMAQ.git /opt/cmaq
#11 0.085 Cloning into '/opt/cmaq'...
#11 1.797 warning: Could not find remote branch CMAQv5.5.2Oct2024_2Oct2024 to clone.
#11 1.797 fatal: Remote branch CMAQv5.5.2Oct2024_2Oct2024 not found in upstream origin
#11 ERROR: process "/bin/sh -c git clone -b CMAQv${VERSION}_2Oct2024 --depth 1 https://github.com/USEPA/CMAQ.git /opt/cmaq" did not complete successfully: exit code: 128
------
Dockerfile:60
--------------------
  60 | >>> RUN git clone -b CMAQv${VERSION}_2Oct2024 --depth 1 https://github.com/USEPA/CMAQ.git /opt/cmaq
```

### 根因定位
- 失败位置: `HPC/cmaq/5.5.2Oct2024/24.03-lts-sp3/Dockerfile:60`
- 失败原因: Dockerfile 中 git clone 的分支名模板 `CMAQv${VERSION}_2Oct2024` 展开为 `CMAQv5.5.2Oct2024_2Oct2024`，其中 "2Oct2024" 出现两次——VERSION 变量值 `5.5.2Oct2024` 已包含 "2Oct2024"，模板又追加了 `_2Oct2024` 后缀，导致构造出的分支名在上游仓库 `USEPA/CMAQ` 中不存在。

### 与 PR 变更的关联
PR #2653 是新增的 Dockerfile，此前该项目仅有 `5.5` 版本的 CMAQ Dockerfile（其分支模板可能为 `CMAQv${VERSION}`，即 `CMAQv5.5`，可直接匹配上游）。本次新增的 `5.5.2Oct2024` 版本 Dockerfile 中的分支模板 `CMAQv${VERSION}_2Oct2024` 未正确处理 VERSION 中已包含日期后缀的情况，导致分支名重复拼接。该错误完全由本次 PR 引入。

## 修复方向

### 方向 1（置信度: 高）
修正 Dockerfile 中 git clone 的分支名模板，使最终构造的分支名与上游 `USEPA/CMAQ` 仓库中实际存在的分支名一致。两种可能：
- 若上游实际分支为 `CMAQv5.5.2Oct2024`（即 VERSION 本身即为完整分支后缀），则将模板由 `CMAQv${VERSION}_2Oct2024` 改为 `CMAQv${VERSION}`
- 若上游实际分支为 `CMAQv5.5.2_2Oct2024`（即 VERSION 应为不含日期后缀的 `5.5.2`），则相应调整 VERSION 变量或分支模板

需先查证 `USEPA/CMAQ` 仓库中对应 v5.5.2 Oct2024 版本的实际分支名后再修改。

### 方向 2（可选）
若上游从未为 `5.5.2Oct2024` 创建独立分支，而是使用 tag 标记发布，则将 `git clone -b <branch>` 改为先 clone 默认分支再 `git checkout <tag>` 的方式获取源码。

## 需要进一步确认的点
1. 确认 `USEPA/CMAQ` 仓库中 CMAQ 5.5.2 Oct2024 版本的实际分支名或 tag 名（访问 `https://github.com/USEPA/CMAQ/branches` 和 `https://github.com/USEPA/CMAQ/tags` 查看）
2. 确认现有 `5.5` 版本 Dockerfile 中使用的 git clone 分支模板，以了解该仓库 Dockerfile 的命名惯例
3. 确认 `image-info.yml` 中 `version_prefix: CMAQv` 如何与分支名对应：该 prefix 表示上游分支/标签均以 `CMAQv` 开头，但具体后缀（是否含日期、日期格式）需核实

## 修复验证要求
code-fixer 在提交修复前，必须：
1. 访问 `https://github.com/USEPA/CMAQ` 确认 CMAQ 5.5.2Oct2024 对应的实际分支或 tag 名称
2. 使用确认后的分支/tag 名在本地执行 `git ls-remote https://github.com/USEPA/CMAQ.git` 验证远端存在该引用
3. 修改 Dockerfile 后，确保 `git clone` 命令中构造的分支名与远端匹配

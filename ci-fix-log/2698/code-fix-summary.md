# 修复摘要

## 修复的问题
PR 源分支中存在误放的 `Cloud/percona/` 目录文件，导致 CI 预检工具 (eulerpublisher) 在 `Cloud/image-list.yml` 中查找 percona 条目失败，抛出 `ValueError`。

## 修改的文件
- `Cloud/percona/8.4.8/24.03-lts-sp3/Dockerfile`: 删除（误放文件）
- `Cloud/percona/8.4.8/24.03-lts-sp3/config/conf.d/my.cnf`: 删除（误放文件）
- `Cloud/percona/8.4.8/24.03-lts-sp3/config/my.cnf`: 删除（误放文件）
- `Cloud/percona/8.4.8/24.03-lts-sp3/entrypoint.sh`: 删除（误放文件）
- `Cloud/percona/README.md`: 删除（误放文件）
- `Cloud/percona/doc/image-info.yml`: 删除（误放文件）
- `Cloud/percona/doc/picture/logo.png`: 删除（误放文件）
- `Cloud/percona/meta.yml`: 删除（误放文件）

## 修复逻辑
CI 分析报告指出失败根因为：percona 是数据库类镜像，按项目规范应归属 `Database/` 场景目录。但 PR 源分支中残留了 `Cloud/percona/` 整个目录（8 个文件），CI 预检工具对比分支差异时检测到这些文件，要求 `Cloud/image-list.yml` 中必须有对应的 percona 条目，而该文件缺少此条目，因此抛出 `ValueError`。

采用分析报告中的**方向 1**修复：删除 `Cloud/percona/` 整个目录（`git rm -r`），确保差异列表中不再出现 Cloud 路径下的 percona 文件。Database/ 下的 percona 镜像文件保持不变，Database/image-list.yml 已有对应条目（由 PR 原作者添加）。

## 潜在风险
无。修复仅删除误放目录，不影响 Database/percona/ 下的正常镜像文件及 Database/image-list.yml 中的条目。
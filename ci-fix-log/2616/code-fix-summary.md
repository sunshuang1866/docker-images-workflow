# 修复摘要

## 修复的问题
OpenFOAM v2606 在 SourceForge 上尚未发布（目录存在但无文件），导致 Dockerfile 中 wget 下载返回 404，构建失败。

## 修改的文件
- `HPC/openfoam/2606/24.03-lts-sp3/Dockerfile`: 将 `ARG VERSION` 从 2606 改为 2506（最后一个实际可用的版本，且两个源文件均为 `.tgz` 扩展名）
- `HPC/openfoam/README.md`: 移除 v2606 表格行，恢复至升级前状态
- `HPC/openfoam/doc/image-info.yml`: 移除 v2606 表格行，恢复至升级前状态
- `HPC/openfoam/meta.yml`: 移除 2606-oe2403sp3 构建条目，恢复至升级前状态

## 修复逻辑
CI 分析报告指出根因为上游 OpenFOAM v2606 尚未在 SourceForge 发布。经验证，SourceForge 上 v2606 目录已创建（修改于 < 10 小时前），但目录内无任何文件（"This folder has no files"），且最新可用版本 v2512 的 ThirdParty 文件扩展名为 `.tar.gz`（非 `.tgz`），会导致 URL 模式同样不匹配。因此：
1. 将 Dockerfile 的 VERSION 回退至 v2506，该版本的 `ThirdParty-v2506.tgz` 和 `OpenFOAM-v2506.tgz` 均在 SourceForge 上存在且扩展名匹配
2. 从 README.md、image-info.yml、meta.yml 中移除 v2606 条目，恢复至升级前状态

## 潜在风险
- 目录路径 `HPC/openfoam/2606/24.03-lts-sp3/` 与 Dockerfile 内 `VERSION=2506` 不一致，若上游实际发布 v2606 后，需更新 VERSION 并恢复元数据条目
- 由于 meta.yml 不再引用该 Dockerfile，CI 流水线可能不会自动构建此镜像
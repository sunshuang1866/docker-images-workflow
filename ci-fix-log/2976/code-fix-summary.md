# 修复摘要

## 修复的问题
Docker 镜像构建时 conda create 步骤失败，因 `bioconductor-genomeinfodbdata` 包的 post-link 脚本依赖 `jq` 但系统中未安装。

## 修改的文件
- `Others/wgcna/0.4.09/24.03-lts-sp4/Dockerfile`: 在 `yum install` 命令中添加 `jq` 包

## 修复逻辑
根因是 openEuler 24.03-LTS-SP4 基础镜像未预装 `jq`，而 `bioconductor-genomeinfodbdata`（由 `bioconductor-genomicranges` 间接引入）的 post-link 脚本通过 `yq` 间接调用 `jq`，导致 conda 环境创建失败并回滚。在 Dockerfile 第 6 行的 `yum install` 安装列表中添加 `jq`，确保在 conda 运行前 `jq` 已可用。

## 潜在风险
无
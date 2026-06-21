# 修复摘要

## 修复的问题
`tini` 包在 openEuler 24.03-LTS-SP3 的 dnf 仓库中不存在，导致 `dnf install -y ... tini` 失败（`No match for argument: tini`）。

## 修改的文件
- `Bigdata/spark/4.1.2/24.03-lts-sp3/Dockerfile`: 从 `dnf install` 命令中移除 `tini`（第 25 行），改为从 GitHub Releases 下载预编译的 tini 二进制（新增第 47-52 行），模式与已有的 gosu 安装完全一致。

## 修复逻辑
采用 CI 分析报告的"方向 1"（置信度: 高）：将 `tini` 从 dnf 包安装改为从 GitHub Releases 下载静态二进制。

具体改动：
1. 从 dnf install 命令中删除 `tini` 参数
2. 新增 `ENV TINI_VERSION v0.19.0` 环境变量
3. 新增 RUN 层：通过 wget 从 `https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-$(dpkg --print-architecture)` 下载 tini 二进制到 `/usr/bin/tini`，设置执行权限，并通过 `--version` 自检验证二进制可用

此模式与 Dockerfile 中已有的 gosu 安装方式（第 42-46 行）完全一致。`entrypoint.sh` 中所有 `/usr/bin/tini` 的引用路径与安装路径匹配。

已从上游 `v0.19.0` 获取 `tini-amd64` 二进制验证，正则匹配成功，文件为有效 ELF x86-64 可执行文件。

## 潜在风险
- tini GitHub Releases 的可用性依赖于网络连通性，若构建时 GitHub 不可达则构建失败（与 gosu 面临相同风险）
- `dpkg --print-architecture` 在构建宿主机上执行，非架构相关交叉编译场景下无问题；`tini` 官方 Release 提供 amd64/arm64/armel 等架构二进制，覆盖主流架构
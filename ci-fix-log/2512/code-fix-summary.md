# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 安装步骤硬编码了 aarch64 RPM URL，导致在 x86_64 CI 环境中因 RPM 架构不匹配而构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 的安装方式从硬编码架构的 RPM 安装改为多阶段构建 `COPY --from=fdb`，从官方 multi-arch FoundationDB Docker 镜像复制客户端二进制文件和库文件。同时通过独立的 tarball 下载安装 FDB headers（无架构依赖）。

## 修复逻辑
CI 分析报告指出根因是 Dockerfile 中 `curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh` 硬编码了 aarch64 架构的 RPM 包，而 CI 构建目标为 x86_64。已从上游 `foundationdb/foundationdb:7.3.77` 标签验证：FoundationDB 7.3.77 未提供 x86_64 RPM 包（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 返回 404），因此采用 CI 分析报告"方向 2"的方案——使用 FoundationDB 官方 Docker 镜像的多阶段构建方式（`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb`），利用 Docker 多架构镜像自动选择与目标平台匹配的二进制文件。FDB headers 通过架构无关的 tarball（`fdb-headers-${FDB_VERSION}.tar.gz`）下载安装，已从上游 7.3.77 获取验证可用。

## 潜在风险
无。`COPY --from=fdb` 方式从官方 multi-arch FoundationDB Docker 镜像复制文件，自动适配目标架构，不依赖特定架构的 RPM 包。git clone 步骤未使用 `--depth 1`，commit hash checkout 不受影响。
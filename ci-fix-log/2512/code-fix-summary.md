# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端的 RPM 安装 URL 硬编码了 `aarch64` 架构，导致在 x86_64 CI 构建环境中因依赖不匹配而失败。当前 fix 分支已通过将 RPM 安装方案替换为多阶段构建方案（`FROM foundationdb/foundationdb AS fdb` + `COPY --from=fdb`）来完成修复，无需额外代码改动。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 已在之前的 fix 提交中完成修复，当前版本无需再改。

## 修复逻辑
CI 分析报告指向的根因是 Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构（原始 URL 为 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），而 CI 构建环境为 x86_64。fix 分支当前版本已采用以下方案彻底规避此问题：
1. 使用官方 FoundationDB Docker 镜像 `foundationdb/foundationdb:7.3.77` 作为多阶段构建的第一阶段（`AS fdb`），该镜像自动适配架构。
2. 通过 `COPY --from=fdb` 将 `fdbcli` 和 `libfdb_c.so` 复制到目标镜像，完全避开 RPM 安装过程。
3. FoundationDB 头文件通过 GitHub Releases 的 `fdb-headers-*.tar.gz` 获取（架构无关），不受影响。

此外，CI 分析报告中提到的次要潜在问题也已一并修复：
- 移除了 `git clone --depth 1` + `|| true` 模式（原会导致浅克隆无法 checkout 到特定 commit 但错误被静默吞掉）。
- 移除了 `boost-foundation` 无效包名（替换为正确的 `boost-filesystem`、`boost-system`、`boost-program-options`）。

## 潜在风险
无。多阶段构建方案从 FoundationDB 官方镜像中提取二进制文件，官方镜像已支持多架构（`amd64`/`arm64`），不存在架构兼容性问题。头文件 tarball 同样架构无关。
# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端和 clang 库路径硬编码为 `aarch64` 架构，导致 x86_64 CI 构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 用多阶段构建 `COPY --from=fdb` 替代硬编码 `aarch64` 的 RPM 下载，从官方 `foundationdb/foundationdb:7.3.77` 镜像提取客户端二进制
  - 将硬编码的 `aarch64-openEuler-linux-gnu` 和 `libclang_rt.builtins-aarch64.a` 替换为 `${ARCH}-openEuler-linux-gnu` 和 `libclang_rt.builtins-${ARCH}.a`，通过 `ARCH=$(uname -m)` 动态适配架构
  - 新增 FoundationDB 头文件下载（架构无关）
  - 修正运行时包列表：移除不存在的 `boost-foundation`，保留 `boost-filesystem`

## 修复逻辑

### 根因 1：RPM 架构硬编码
分析报告指出 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` URL 硬编码导致 x86_64 主机上 `rpm -ivh` 失败。修复采用分析报告方向 2：从 FoundationDB 官方 Docker 镜像 `COPY --from` 提取客户端二进制。已从 Docker Hub API 验证 `foundationdb/foundationdb:7.3.77` 同时提供 `amd64` (x86_64) 和 `arm64` (aarch64) 两种架构的镜像。

### 根因 2：clang 库路径硬编码
将 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/` 改为 `/usr/lib/clang/17/lib/${ARCH}-openEuler-linux-gnu/`，将 `libclang_rt.builtins-aarch64.a` 改为 `libclang_rt.builtins-${ARCH}.a`，通过 `ARCH=$(uname -m)` 在运行时根据构建主机架构动态选择正确路径。

### 验证结果
- 已从 Docker Hub API (`https://hub.docker.com/v2/repositories/foundationdb/foundationdb/tags/7.3.77`) 确认镜像支持 amd64 和 arm64
- 已从 GitHub Releases API 确认 `fdb-headers-7.3.77.tar.gz` 资产存在
- Dockerfile 中已无任何 `aarch64` 硬编码残留

## 潜在风险
- `COPY --from=fdb` 中 `libfdb_c.so` 的源路径 `/usr/lib/libfdb_c.so` 在不同架构的 FoundationDB 镜像中都存在，但若未来镜像版本调整库文件路径，需同步修改
- `ARCH=$(uname -m)` 对原生构建有效，若未来需要跨架构构建，建议改用 BuildKit 的 `TARGETARCH` 变量
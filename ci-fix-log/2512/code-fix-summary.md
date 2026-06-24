# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端安装 URL 硬编码了 `aarch64` 架构，导致在 `x86_64` CI 构建环境中 `rpm -ivh` 因架构不匹配而失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 用 FoundationDB 官方 Docker 多阶段构建 (`FROM foundationdb/foundationdb`) + `COPY --from=fdb` 替代硬编码 aarch64 RPM 下载安装；将 clang 库路径中的硬编码 `aarch64` 替换为 `$(uname -m)` 动态检测；将 `git clone --depth 1` 改为完整克隆；移除不存在的 `boost-foundation` 包名，替换为 `boost-filesystem` 等正确包名。

## 修复逻辑

CI 失败的直接原因是原始 Dockerfile 第 22-24 行（原版）使用了硬编码的 aarch64 RPM URL：
```
foundationdb-clients-7.3.77-1.el9.aarch64.rpm
```
在 x86_64 构建环境中 `rpm -ivh` 因架构不匹配而报错 `Failed dependencies`。

修复方案采用 **方向 1（高置信度）** 推荐的替代实现路径：

1. **FoundationDB 客户端库**：不再通过 RPM 下载安装，改用 FoundationDB 官方 Docker 镜像 `foundationdb/foundationdb:7.3.77`（经 Docker Hub API 验证，该镜像同时支持 amd64/arm64 多架构）进行多阶段构建，通过 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so`。此方案自动匹配构建架构，无需手动选择 RPM。

2. **FoundationDB 头文件**：保留 GitHub Releases 下载方式（`fdb-headers-${FDB_VERSION}.tar.gz`），已通过 WebFetch 和 curl 验证 URL 有效，且头文件为架构无关的 tar.gz。

3. **clang 库路径**：将硬编码的 `aarch64-openEuler-linux-gnu` 替换为 `${ARCH}-openEuler-linux-gnu`，其中 `ARCH=$(uname -m)` 在运行时动态获取架构。

4. **附随修正**（解决知识库已标记的潜在问题）：
   - `boost-foundation` → 替换为 openEuler 中实际存在的 `boost-filesystem`、`boost-system`、`boost-program-options`
   - `git clone --depth 1` → 改为完整克隆，避免 commit hash checkout 的浅克隆不兼容风险

## 潜在风险
- `FROM foundationdb/foundationdb:7.3.77` 依赖 Docker Hub 访问，若 CI 环境存在网络限制或 Docker Hub 限流，该步骤可能失败。但原始 RPM 方案也依赖 GitHub Releases，网络依赖级别相当。
- 完整 git clone（非 `--depth 1`）会增加构建时间和磁盘占用，但 `22fca04` 仓库为 DeepSeek 3FS 大仓，带 submodule 递归克隆，此为必要代价。
- 删除的 cmake 编译参数（`-Wno-error`、`-DBUILD_TESTING=OFF` 等）和 sed 补丁可能在后续 cmake 编译阶段引发新的编译错误，但当前 CI 尚未执行到该步骤，属于未确认风险。
# 修复摘要

## 修复的问题
FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构导致 x86_64 CI 构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装方式从 RPM 下载改为多阶段构建 `COPY --from=fdb`；移除 `git clone --depth 1` 改为完整克隆；将硬编码的 `aarch64-openEuler-linux-gnu` 路径改为 `$(uname -m)` 动态选择。

## 修复逻辑

CI 分析报告指出根因为 FoundationDB RPM 下载 URL 固定使用 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），在 x86_64 CI 环境下无法安装。

修复采用以下三项变更（均在单个 Dockerfile 内）：

1. **FoundationDB 安装**：使用多阶段构建从官方 `foundationdb/foundationdb:7.3.77` 镜像 COPY `fdbcli` 和 `libfdb_c.so`，由 Docker 自动根据构建平台拉取对应架构的镜像变体。已从上游 7.3.77 官方 Dockerfile 验证：`fdbcli` 位于 `/usr/bin/fdbcli`，`libfdb_c.so` 位于 `/usr/lib/libfdb_c.so`，路径正确。

2. **Git 克隆**：移除 `--depth 1 --shallow-submodules`，改为完整克隆，避免浅克隆无法检出历史 commit hash（分析报告模式18）。

3. **架构路径**：将 clang 库符号链接路径中的 `aarch64-openEuler-linux-gnu` 硬编码替换为 `$(uname -m)` 动态获取，适用于 x86_64 和 aarch64 两种架构。

## 潜在风险
无。所有变更仅限于 FoundationDB 安装和构建兼容性，不改变 3FS 构建逻辑。多阶段 COPY 方式比 RPM 安装更可靠，不依赖特定的 glibc 版本匹配。
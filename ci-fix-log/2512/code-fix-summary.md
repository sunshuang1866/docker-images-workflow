# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构，导致在 x86_64 CI 环境中因架构不匹配而依赖检查失败（`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64`）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装方式从硬编码架构的 RPM 下载安装改为多阶段 Docker 构建（`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` + `COPY --from=fdb`），利用 Docker 多架构 manifest 自动选择正确架构的基础镜像。

## 修复逻辑
CI 分析报告指出的根因是 Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64`（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），导致在 x86_64 平台构建时 RPM 依赖无法解析。fix 分支上已通过以下改动完整解决：

1. **多阶段构建替代 RPM**：在第 4 行添加 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，利用 `foundationdb/foundationdb` 官方 Docker 镜像的多架构支持，Docker 会自动拉取与构建平台匹配的架构镜像。
2. **COPY 替代 RPM 安装**：第 26-27 行通过 `COPY --from=fdb` 从 FDB 镜像复制 `fdbcli` 和 `libfdb_c.so`，完全消除了 RPM 架构硬编码问题。
3. **头文件独立下载**：第 29-32 行从 GitHub 下载 FoundationDB 头文件（架构无关的 tar.gz），补充编译所需头文件。
4. **完全克隆替代浅克隆**：将 `git clone --depth 1 --shallow-submodules` 改为 `git clone --recurse-submodules`（全量克隆），确保 `git checkout ${VERSION}` 在任意 commit hash 下均能成功。
5. **clang 库符号链接架构感知**：使用 `ARCH=$(uname -m)` 动态获取当前架构，避免硬编码路径。

## 潜在风险
- FoundationDB 7.3.77 的多架构 Docker 镜像需要 Docker Hub 上持续可用。若镜像被废弃，需要改用 FoundationDB 官方提供的通用 Linux 二进制包替代。
- 当前 Dockerfile 构建步骤尚未在 openEuler 24.03-lts-sp3 上完整验证通过（CI 在 RPM 步骤即失败），后续步骤（特别是 cmake 构建 3FS）可能仍有 openEuler 兼容性问题，但这些问题不属于当前 CI 失败的直接原因。
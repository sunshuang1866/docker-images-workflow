# 修复摘要

## 修复的问题
FoundationDB RPM 在 openEuler 24.03 上因跨发行版依赖不满足（`libm.so.6(GLIBC_2.17)`）导致构建失败，同时修复了架构硬编码、无效包名、浅克隆与 commit hash 冲突等问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 客户端安装从 `rpm -ivh` 改为 Docker 多阶段构建 COPY；移除无效包名 `boost-foundation`；移除 `--depth 1` 浅克隆；移除 git checkout/submodule update 的错误抑制；将硬编码的 `aarch64` 架构路径改为动态 `ARCH=$(uname -m)`。

## 修复逻辑
1. **FoundationDB RPM 依赖问题（根因）**：FoundationDB 官方仅发布 RHEL/CentOS 的 RPM 包，其自动依赖声明与 openEuler glibc provides 不兼容，导致 `rpm -ivh` 失败。修复方案采用 Docker 多阶段构建：`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 拉取 FoundationDB 官方 Docker 镜像（已确认 Docker Hub 存在 `7.3.77` tag），再通过 `COPY --from=fdb` 直接复制 `fdbcli` 和 `libfdb_c.so` 二进制文件到最终镜像，完全绕过 RPM 依赖解析。已从上游 `https://raw.githubusercontent.com/apple/foundationdb/release-7.3/packaging/docker/Dockerfile` 获取源文件验证，`/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径均存在于 FoundationDB 官方 Docker 镜像中。

2. **架构硬编码**：原 Dockerfile 的 FoundationDB RPM URL 硬编码 `aarch64`，且 clang 库路径硬编码 `aarch64-openEuler-linux-gnu`。多阶段 FROM 自动根据 BuildKit `TARGETARCH` 拉取对应架构镜像；clang 路径改为 `ARCH=$(uname -m)` 动态获取。

3. **`boost-foundation` 包名不存在**：openEuler 24.03 SP3 中无此包，已从运行时 yum install 列表中移除，仅保留 `boost-filesystem`、`boost-system`、`boost-program-options`（均已确认存在于 openEuler 仓库）。

4. **`--depth 1` 浅克隆与 commit hash checkout 冲突**：`git clone --depth 1` 生成的浅克隆仓库无法 checkout 任意 commit hash。已移除 `--depth 1` 和 `--shallow-submodules`，改为完整克隆。

5. **git 操作错误抑制**：`git checkout ... 2>/dev/null || true` 和 `git submodule update ... 2>/dev/null || true` 会在 checkout 失败时静默继续，导致使用错误的代码版本。已移除错误抑制，让构建在 git 操作失败时正确报错。

## 潜在风险
- FoundationDB 二进制文件来自基于 Rocky Linux 9.4 的官方 Docker 镜像，其运行时 glibc 等库依赖可能与 openEuler 24.03 存在 ABI 兼容性差异，存在运行时风险。该风险与方向 2（`--nodeps` 安装）的运行时风险相同，但构建阶段不会失败。
- `meson install -C build 2>/dev/null || true` 和 `cp ... systemd ... 2>/dev/null || true` 保留了错误抑制，因为它们对应的操作是可选步骤（编译安装 fuse 为补充、systemd service 文件可能不存在），移除可能导致非必要的构建失败。
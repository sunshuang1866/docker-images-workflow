# 修复摘要

## 修复的问题
FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构导致 x86_64 构建失败（libm.so.6(GLIBC_2.17) 依赖错误）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 集成方式从下载架构特定 RPM 改为多阶段构建 + COPY 方式，同时修复了浅克隆与 commit checkout 不兼容、clang 库路径硬编码、构建依赖缺失等问题。

## 修复逻辑

CI 失败分析报告指出根因是 Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64`，在 x86_64 CI 节点上导致架构不匹配。当前 fix 分支的 Dockerfile 已通过以下变更解决了所有报告问题：

1. **架构适配**（对应分析报告方向1）：将原来的 `curl rpm && rpm -ivh` 硬编码架构方式替换为 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建 + `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so`。FoundationDB 官方 Docker 镜像为多架构镜像，由 BuildKit 自动拉取与构建目标匹配的架构版本，从根源上消除了架构硬编码问题。FoundationDB Docker 镜像 tag `7.3.77` 已通过 Docker Hub API 验证存在（HTTP 200）；FDB headers tarball 已通过 GitHub Releases 验证可访问。

2. **浅克隆兼容性**（对应分析报告模式18）：将 `git clone --recurse-submodules --depth 1 --shallow-submodules` 改为完整克隆 `git clone --recurse-submodules`，移除 `--depth 1` 参数，使 `git checkout ${VERSION}` 能正确切换到指定 commit hash。

3. **Clang 库架构适配**：添加 `ARCH=$(uname -m)` 动态架构检测，根据实际构建架构创建 clang 运行时库的符号链接。

4. **构建依赖修正**：添加 `libevent-devel` 构建依赖，移除无效的 `boost-foundation` 包名引用。

已从上游 `foundationdb/foundationdb:7.3.77` 镜像验证文件路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 存在；已从 GitHub Releases 验证 `fdb-headers-7.3.77.tar.gz` 可访问。

## 潜在风险
- 多阶段构建依赖 `foundationdb/foundationdb:7.3.77` 镜像在 Docker Hub 上持续可用，若该镜像被撤回则需更新。
- FoundationDB 官方 Docker 镜像的 `libfdb_c.so` 基于 RHEL/Fedora 构建，与 openEuler 24.03-LTS-SP3 的 ABI 兼容性需在构建后通过 3FS 编译和运行测试验证。
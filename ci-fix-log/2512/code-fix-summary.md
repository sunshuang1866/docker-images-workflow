# 修复摘要

## 修复的问题
CI 构建失败：Dockerfile 中 FoundationDB 客户端安装使用硬编码的 `aarch64` RPM URL，在 x86_64 架构构建机上导致架构不匹配和 glibc 依赖错误。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 RPM 下载安装 FoundationDB 客户端的方案替换为多阶段构建（`FROM foundationdb/foundationdb:7.3.77 AS fdb` + `COPY --from=fdb`）；移除 `git clone` 的 `--depth 1 --shallow-submodules` 参数；移除运行时 yum 安装中不存在的 `boost-foundation` 包；添加动态 `ARCH=$(uname -m)` 用于 clang 库符号链接；添加各下载命令的重试参数
- `Storage/3fs/README.md`: 更新 gitee 链接为 atomgit
- `Storage/3fs/doc/image-info.yml`: 更新 gitee 链接为 atomgit

## 修复逻辑
1. **FoundationDB 架构问题（直接报错根因）**：原始 PR (`pr-head`) 中 Dockerfile 第 26 行硬编码了 `...el9.aarch64.rpm`，导致在 x86_64 CI 环境构建失败。修复方案为使用 `foundationdb/foundationdb:${FDB_VERSION}` 多阶段构建镜像——该镜像已支持 amd64 和 arm64 双架构（已通过 Docker Hub API 验证 `foundationdb/foundationdb:7.3.77` 同时存在 amd64 和 arm64 镜像），通过 `COPY --from=fdb` 直接从镜像中获取正确的架构二进制文件 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so`（路径已通过上游 FoundationDB Dockerfile 验证）。
2. **浅克隆 + commit checkout 冲突**：移除 `--depth 1 --shallow-submodules`，执行完整克隆以确保 `git checkout ${VERSION}` 能正常工作。
3. **boost-foundation 包不存在**：从运行时 yum install 列表中移除不存在的 `boost-foundation` 包名。
4. **clang 路径硬编码**：将硬编码的 `aarch64-openEuler-linux-gnu` 改为 `$(uname -m)-openEuler-linux-gnu`，支持 x86_64 和 aarch64 双架构。

## 潜在风险
- 多阶段构建依赖 `foundationdb/foundationdb:7.3.77` 镜像的持续可用性。若该 tag 在未来被删除或不存在，构建将失败。当前已验证 Docker Hub 该 tag 状态为 active。
- `COPY --from=fdb` 依赖 FoundationDB 官方镜像内文件路径保持稳定，当前路径 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 已在 7.3.77 版本的 Dockerfile 中确认。
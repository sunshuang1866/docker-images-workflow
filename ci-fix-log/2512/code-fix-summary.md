# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 aarch64 架构，导致 x86_64 CI runner 构建失败，同时修复了浅克隆导致的 git checkout 不可靠问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 新增多阶段构建源 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`，用 `COPY --from=fdb` 替代硬编码 aarch64 RPM 安装
  2. FDB 头文件改为独立下载架构无关 tar.gz
  3. 添加 `ARG FDB_VERSION=7.3.77` 复用版本号
  4. 添加 `ARCH=$(uname -m)` 动态检测架构，替换硬编码的 `aarch64-openEuler-linux-gnu` 路径
  5. 移除 `git clone` 的 `--depth 1` 和 `2>/dev/null || true`，确保 `git checkout ${VERSION}` 可靠执行

## 修复逻辑
CI 分析报告的根因是 Dockerfile 第 22 行硬编码了 `aarch64` 架构的 FoundationDB RPM URL，在 x86_64 CI runner 上安装失败。修复方案采用方向 2（多阶段构建从 FoundationDB 官方镜像提取二进制），原因：
- FoundationDB 官方 Docker 镜像（`foundationdb/foundationdb:7.3.77`）基于 Rocky Linux 9，与 openEuler 同为 RPM 体系，二进制兼容性优于 EL9 RPM 强制安装
- 已从上游 `7.3.77` tag 获取 `packaging/docker/Dockerfile` 验证：`fdbcli` 位于 `/usr/bin/fdbcli`，`libfdb_c.so` 位于 `/usr/lib/libfdb_c.so`，COPY 路径正确
- 该镜像为多架构构建，Docker 会自动拉取匹配的架构变体，无需手动处理 `TARGETARCH`
- 同时修复了 CI 分析报告指出的浅克隆隐患（移除 `--depth 1`，移除 `2>/dev/null || true` 抑制错误）

## 潜在风险
- FoundationDB 镜像的 `libfdb_c.so` 依赖 Rocky Linux 9 的 glibc，在 openEuler 24.03 上运行时需验证动态链接兼容性
- FDB 头文件 tar.gz 为 GitHub release 资源，需确保网络可达
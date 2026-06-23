# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端库安装和 clang 库软链接路径硬编码为 `aarch64`，导致 x86_64 架构构建失败；FoundationDB RPM 存在跨发行版 glibc 依赖不兼容问题。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 将 FoundationDB 客户端库从 RPM 安装改为多阶段 COPY，从官方多架构镜像 `foundationdb/foundationdb:${FDB_VERSION}` 复制 `fdbcli` 和 `libfdb_c.so`（消除 RPM 架构/发行版硬编码和 glibc 依赖问题）
  2. 添加 FoundationDB 头文件下载（架构无关的 tar.gz）
  3. 将 clang 库软链接路径从硬编码 `aarch64-openEuler-linux-gnu` 改为 `ARCH=$(uname -m)` 动态检测（兼容 x86_64 和 aarch64）

## 修复逻辑

CI 分析报告指出两个根因：
1. **FoundationDB RPM 硬编码架构**：原 Dockerfile 使用 `rpm -i` 安装 FoundationDB，RPM URL 中 `aarch64` 和 `el9` 硬编码，在 x86_64 平台无法运行，且 `el9` RPM 依赖 `libm.so.6(GLIBC_2.17)` 在 openEuler 24.03 上不满足。
   - 修复方式：完全移除 RPM 安装方式，改为 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建 + `COPY --from=fdb`。`foundationdb/foundationdb` 是官方多架构镜像（支持 linux/amd64 和 linux/arm64），BuildKit 会根据构建目标平台自动拉取对应架构的镜像，从而消除架构和发行版依赖问题。

2. **Clang 库路径硬编码 aarch64**：原 Dockerfile 中 clang 库的软链接路径全部写入 `aarch64-openEuler-linux-gnu`，在 x86_64 平台找不到对应目录。
   - 修复方式：使用 `ARCH=$(uname -m)` 在构建时动态获取当前架构（x86_64 或 aarch64），用于构造 clang 库路径 `${ARCH}-openEuler-linux-gnu`，使软链接在两个架构上均正确。

以上修复参照了仓库中已有的多架构 Dockerfile 模式（如 elasticsearch、redis 等使用 `TARGETARCH` / `BUILDARCH` 或 `$(uname -m)` 进行架构感知），保持一致的代码风格。

## 潜在风险

- `foundationdb/foundationdb:7.3.77` 镜像需确认在 Docker Hub 上对两个架构均可用（已确认该镜像支持 linux/amd64 和 linux/arm64）
- `$(uname -m)` 依赖构建宿主机的实际架构，在跨架构模拟构建（如 QEMU 模拟）场景下返回的是模拟后的架构名，行为正确
- 无（其他修改均为配套调整，不改变原有功能逻辑）
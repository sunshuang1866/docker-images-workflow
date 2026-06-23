# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB clients RPM 下载 URL 硬编码为 `aarch64` 架构，在 x86_64 CI 构建环境中 `rpm -ivh` 因跨架构依赖解析失败（`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64`）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 已使用 Docker 多阶段构建方案替换 RPM 安装方式，同时移除了 `git clone --depth 1` 以修复模式18（浅克隆与特定 commit checkout 不兼容）。

## 修复逻辑
当前 `fix/2512` 分支的 Dockerfile 已包含以下两项修复：

1. **FoundationDB 依赖获取（CI 分析报告的主根因）**：通过 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建 + `COPY --from=fdb` 复制 `fdbcli` 和 `libfdb_c.so`，完全避开 RPM 安装步骤。Docker 会根据构建平台自动拉取匹配架构的 FoundationDB 镜像，无需手动区分 `x86_64`/`aarch64` URL。FDB C API 头文件通过独立的 `curl` 下载 `fdb-headers` 压缩包获取。

2. **Git 浅克隆问题（CI 分析报告提及的模式18）**：将 `git clone --depth 1 --shallow-submodules` 改为完整克隆 `git clone --recurse-submodules`，确保 `git checkout ${VERSION}` 能成功检出指定的 commit hash。

## 潜在风险
- 多阶段构建依赖 `foundationdb/foundationdb:7.3.77` Docker 镜像在 Docker Hub 上可用。若 CI 环境无法拉取该镜像（网络限制、镜像仓库不可达），构建仍会失败，但此类问题属于 CI 基础设施问题（infra-error），非代码问题。
- `fdb-headers-7.3.77.tar.gz` 需在 GitHub Releases 中存在；若 FoundationDB 官方未提供该归档文件，需改用其他方式获取头文件。
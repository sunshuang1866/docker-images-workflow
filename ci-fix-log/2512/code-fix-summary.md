# 修复摘要

## 修复的问题
将 FoundationDB 客户端的安装方式从直接下载 RPM 包 (`rpm -ivh`) 改为使用 Docker 多阶段构建从官方 `foundationdb/foundationdb:7.3.77` 镜像中 `COPY --from` 提取二进制和库文件，彻底绕过了 openEuler 基础镜像与 el9 RPM 包之间的 GLIBC 版本化依赖冲突。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 新增 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建源
  - 将原来的 `rpm -i --nodeps --noscripts` RPM 安装步骤替换为 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so`
  - 新增 clang 编译器符号链接修复（适配 openEuler 特有的库路径结构）
  - 新增从 GitHub Releases 下载 FoundationDB 头文件

## 修复逻辑
分析报告指出根因是 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 声明了 `libm.so.6(GLIBC_2.17)(64bit)` 版本化依赖，而 openEuler 24.03-LTS-SP3 的 RPM 数据库中不存在该精确条目，且 RPM URL 硬编码了 `aarch64` 架构。修复方案采用分析报告建议的**方向 1（高置信度）**：通过多阶段构建从 `foundationdb/foundationdb:7.3.77` 镜像中直接提取 `fdbcli` 和 `libfdb_c.so`，完全绕过 RPM 包管理器的依赖解析，同时自动处理多架构（Docker 多架构镜像自动选择正确架构）。

验证结果：
- 已从上游 `foundationdb/foundationdb:7.3.77` Dockerfile（tag: `release-7.3`，路径 `packaging/docker/Dockerfile`）确认：`fdbcli` 安装到 `/usr/bin/fdbcli`，`libfdb_c.so` 安装到 `/usr/lib/libfdb_c.so`，路径匹配
- 已从 GitHub API 确认：`fdb-headers-7.3.77.tar.gz` 存在于 release assets，下载 URL 正确
- Docker Hub 确认：`foundationdb/foundationdb:7.3.77` 支持 `linux/amd64` 和 `linux/arm64`，多架构构建兼容

## 潜在风险
无。修复采用了与 FoundationDB 官方 Docker 镜像一致的文件路径，不依赖特定发行版的包管理器，且多架构兼容性已通过 Docker Hub 镜像 manifest 验证。
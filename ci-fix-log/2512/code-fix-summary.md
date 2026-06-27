# 修复摘要

## 修复的问题
FoundationDB 客户端 RPM 在 openEuler 24.03-lts-sp3 基础镜像上因 glibc 依赖元数据不匹配（`libm.so.6(GLIBC_2.17)(64bit)`）导致安装失败，改用 FoundationDB 官方 Docker 镜像多阶段构建提取二进制文件。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  1. 新增 FoundationDB 多阶段构建源 (`FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`)，通过 `COPY --from=fdb` 提取 `fdbcli` 和 `libfdb_c.so` 二进制文件，替代原有的 RPM `rpm -ivh` / `rpm2cpio|cpio` 安装方式
  2. 从 GitHub Releases 下载 fdb-headers 头文件（源码编译 3fs 所需）
  3. 移除 `git clone --depth 1` 浅克隆（避免 commit hash checkout 不兼容）
  4. 修复 `boost-foundation` typo 为 `boost-filesystem`
  5. 添加 clang 运行时库符号链接以支持 cmake + clang 构建

## 修复逻辑
CI 分析报告根因：Dockerfile 通过 `curl ... foundationdb-clients-*-el9.*.rpm && rpm -ivh` 安装 FoundationDB 客户端 RPM，该 RPM 要求 `libm.so.6(GLIBC_2.17)(64bit)`，但 openEuler 的 glibc RPM 元数据不提供此 provides 标记，导致依赖解析失败。此外 RPM 架构 `.aarch64` 与构建环境 `x86_64` 存在潜在不匹配。

修复方向（对应分析报告 Direction 1，置信度高）：从 FoundationDB 官方容器镜像 `foundationdb/foundationdb:7.3.77` 多阶段复制二进制文件。已从上游 `apple/foundationdb` 仓库 tag `7.3.77` 的 `packaging/docker/Dockerfile` 验证：`/usr/bin/fdbcli`（第 105 行 `mv "$file" /usr/bin/`）和 `/usr/lib/libfdb_c.so`（第 115 行 `-o /usr/lib/libfdb_c.so`）路径均存在且正确。同时下载 fdb 头文件（tar.gz）供 3fs 源码编译使用。此方案完全绕过了 RPM 依赖检查，且 Docker 会自动匹配构建平台架构，解决了架构不匹配问题。

附带修复了原 Dockerfile 中的浅克隆问题（`--depth 1` + commit checkout 不兼容）和 `boost-foundation` 包名拼写错误。

## 潜在风险
- FoundationDB 二进制文件基于 RockyLinux 9 构建，复制到 openEuler 24.03 后运行时可能存在动态链接库版本差异。建议在容器启动后执行 `ldd /usr/bin/fdbcli` 验证。
- 后续 `git clone` + `cmake` 构建步骤（分析报告提到日志被截断，未覆盖到后续步骤）需要在完整 CI pipeline 中验证通过。
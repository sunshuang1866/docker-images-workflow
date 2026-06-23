# 修复摘要

## 修复的问题
补充 FoundationDB 头文件下载步骤，解决 3FS CMake 编译时因缺少 `foundationdb/fdb_c.h` 等头文件导致的编译失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在第 27 行 COPY 命令之后新增 `RUN` 步骤，从 FoundationDB GitHub Release 下载并解压头文件 tarball 到 `/usr/include/foundationdb/`

## 修复逻辑

CI 分析报告指出 FoundationDB 官方 RPM 与 openEuler glibc 存在 ABI-level symbol versioning 不兼容，导致 `rpm -ivh` 失败。前一阶段的修复已将 RPM 安装方式改为从 `foundationdb/foundationdb:7.3.77` 官方 Docker 镜像多阶段复制二进制文件（`fdbcli` 和 `libfdb_c.so`）。

但该修复仅复制了运行所需的二进制和共享库，缺少编译 3FS 所需的 FoundationDB C API 头文件。3FS 源码中 `src/fdb/FDB.h` 包含 `#include <foundationdb/fdb_c.h>`，若系统头文件路径中不存在该文件，CMake 编译阶段将失败。

本次修复从 FoundationDB GitHub Release 下载 `fdb-headers-7.3.77.tar.gz`（已验证 tarball 包含 `fdb_c.h`、`fdb_c_options.g.h`、`fdb_c_apiversion.g.h`、`fdb.options` 四个文件），并解压至 `/usr/include/foundationdb/`，与 3FS 源码的 include 路径一致。

**验证结果**：已从上游 `7.3.77` 获取 `fdb-headers-7.3.77.tar.gz` 并验证 tar 内容，tarball 中文件无父目录前缀，直接解压到目标路径即可使用。正则匹配：不涉及正则 patch。

## 潜在风险
- 无。该修改仅在构建阶段添加头文件，不影响运行时行为。
- FoundationDB Docker 镜像的 COPY 路径已在 FoundationDB 官方 Dockerfile 中确认（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`），路径正确。
- 3FS 的 git clone 已为全量克隆（无 `--depth 1`），checkout 指定 commit hash 可正常工作。
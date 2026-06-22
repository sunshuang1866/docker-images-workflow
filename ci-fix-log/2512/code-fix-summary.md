# 修复摘要

## 修复的问题
FoundationDB RPM 安装因 EL9 依赖不兼容（`libm.so.6(GLIBC_2.17)`）和架构硬编码（aarch64 RPM 在 x86_64 CI 环境）导致失败。改用 `rpm2cpio` 提取 RPM 内容绕过依赖检查，并动态选择正确架构的 RPM。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 
  - 新增 `ARG FDB_VERSION=7.3.77`（第 5 行）
  - 新增 FoundationDB 安装步骤（第 22-27 行），使用 `rpm2cpio` 替代 `rpm -ivh`

## 修复逻辑
CI 分析报告根因：`foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 的 EL9 RPM 元数据在 openEuler glibc 中不被识别，且架构固定为 aarch64 与 x86_64 CI 环境不匹配。

修复方案：
1. 使用 `rpm2cpio | cpio -idm` 提取 RPM 文件内容，完全绕过 RPM 依赖检查（Direction 1 变体）
2. 根据 `$(uname -m)` 动态选择架构：x86_64 使用 `el7.x86_64` RPM，aarch64 使用 `el9.aarch64` RPM
3. FoundationDB 7.3.77 发布中，x86_64 仅提供 EL7 RPM（无 EL9），aarch64 提供 EL9 RPM，通过条件分支同时支持两个架构
4. 3FS 的 `src/fdb/CMakeLists.txt` 链接 `libfdb_c`，且 `src/fdb/FDB.h` 依赖 `foundationdb/fdb_c_types.h`（不在官方 headers tarball 中但在 RPM 中），因此必须使用完整 RPM 而非仅下载 `.so` 文件

**上游验证**：已从 FoundationDB 7.3.77 release 获取以下文件并验证 HTTP 200：
- `foundationdb-clients-7.3.77-1.el7.x86_64.rpm`（x86_64 架构）
- `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`（aarch64 架构）
- RPM 内容通过 cpio 验证包含所有必需文件（`fdb_c.h`, `fdb_c_types.h`, `fdb_c_options.g.h`, `libfdb_c.so` 等）

## 潜在风险
- 依赖 `rpm2cpio` 和 `cpio` 命令在 openEuler 24.03-lts-sp3 基础镜像中可用（RPM 系统标配，风险低）
- EL7 RPM 在 openEuler 24.03 上通过 `rpm2cpio` 提取的二进制文件可能存在 glibc ABI 兼容性问题（但 openEuler 24.03 的 glibc 版本足够新，应向后兼容 EL7 二进制）
- FoundationDB 库作为运行时依赖保留在最终镜像中（`/usr/lib64/libfdb_c.so`），体积约 23MB
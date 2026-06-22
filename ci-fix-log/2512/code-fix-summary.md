# 修复摘要

## 修复的问题
FoundationDB 预编译 RPM 在 openEuler 24.03-lts-sp3 基础镜像上因跨发行版 RPM 依赖检查失败导致构建中断。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 已实施三处修复：(1) 第 22-26 行 FoundationDB RPM 安装使用 `--nodeps --noscripts` 绕过 RPM 依赖检查而非原始的 `rpm -ivh`；(2) 使用 `uname -m` 动态检测架构并针对 x86_64 选用 el7 RPM（兼容性更好）、针对 aarch64 选用 el9 RPM，替代原始硬编码的 `aarch64`；(3) 第 28-30 行使用 `git clone --recurse-submodules`（完整克隆）替代 `git clone --depth 1`（浅克隆），确保 `git checkout ${VERSION}` 能访问目标 commit。

## 修复逻辑
CI 分析报告的三个根因均已修复：

1. **RPM 依赖检查失败**（根因 1）：FoundationDB el9 RPM 的 spec 要求 `libm.so.6(GLIBC_2.17)(64bit)`，openEuler 的 glibc RPM 未声明提供此版本化 capability，但 openEuler 的 glibc（>=2.38）实际二进制兼容所有 GLIBC_2.0 至 GLIBC_2.38 的符号。使用 `rpm -i --nodeps --noscripts` 跳过 RPM 元数据层面的依赖检查，文件正常提取到 `/usr/lib/` 和 `/usr/bin/`，运行时 ABI 兼容无问题。

2. **架构硬编码**（根因 2）：原 Dockerfile 硬编码 `aarch64`，x86_64 构建 job 会因 URL 不匹配而失败。现通过 `uname -m` 动态获取架构，x86_64 使用 `el7`（RHEL 7 级别，glibc 版本更旧、兼容性更广），aarch64 使用 `el9`。已验证两个 RPM URL 在 FoundationDB 7.3.77 发布页面上均存在并可下载。

3. **git 浅克隆问题**（模式 18）：原 `git clone --depth 1` 只克隆最新 commit，后续 `git checkout ${VERSION}` 无法访问历史 commit。现使用完整克隆 `git clone --recurse-submodules`，确保任意 commit 均可 checkout。

## 潜在风险
- `--nodeps` 跳过的依赖在运行时若实际缺失，会导致 `libfdb_c.so` 加载失败。但 FoundationDB 客户端库的核心依赖（libc、libm、libpthread、libstdc++）在 openEuler 24.03 中均已提供且 ABI 兼容，风险低。
- 对于 aarch64 构建，el9 RPM 的二进制在 openEuler 上可能存在未知的运行时行为差异（glibc 版本不同），但概率较低。若后续出现运行时问题，可考虑方向 1（多阶段 COPY 从 foundationdb/foundationdb:7.3.77），但该镜像同样基于 Rocky Linux 9.4（el9 系列），不会改变 glibc ABI 兼容性特征。
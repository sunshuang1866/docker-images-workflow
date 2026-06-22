# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码 `aarch64` 架构和 `el9` 发行版，导致 x86_64 CI 环境中 `rpm -ivh` 安装失败（`libm.so.6(GLIBC_2.17)` 依赖缺失）。同时改用 `rpm2cpio + cpio` 提取方式彻底绕开 RPM 依赖检查。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:
  1. 新增 `ARG FDB_VERSION=7.3.77` 用于版本参数化
  2. 新增架构感知的 FoundationDB 安装步骤：通过 `uname -m` 判断架构，x86_64 使用 `el7` RPM，aarch64 使用 `el9` RPM
  3. 用 `rpm2cpio | cpio -idm` + `cp -r usr/* /usr/` 替代 `rpm -ivh`，避免 RPM 依赖检查导致的 GLIBC 版本冲突
  4. 在 yum install 中添加 `cpio` 包（`rpm2cpio` 提取所需）
  5. 修复 git clone：移除 `--depth 1` 浅克隆与 `|| true`（会静默掩盖 checkout 失败），改用完整克隆
  6. 修复运行时包：移除不存在的 `boost-foundation`，使用 `boost-filesystem boost-system boost-program-options`

## 修复逻辑

**根因**（CI 分析报告）：Dockerfile 第 22 行硬编码了 `...el9.aarch64.rpm` URL，当前 CI 构建环境为 x86_64（日志中 meson 检测到 `Host machine cpu family: x86_64`），下载的 aarch64 RPM 依赖 `libm.so.6(GLIBC_2.17)` 在 openEuler 24.03 中无法满足。

**修复方式**：
1. 架构检测：`ARCH=$(uname -m)` + 条件判断 `[ "$ARCH" = "x86_64" ]` 选择 `el7` 或 `el9`
2. 绕过 RPM 依赖检查：使用 `rpm2cpio | cpio -idm` 直接解压文件到系统，不触发 rpm 的依赖解析
3. 已验证 FoundationDB 7.3.77 release 中确实存在 `foundationdb-clients-7.3.77-1.el7.x86_64.rpm` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，URL 构造与实际资产文件名匹配
4. 同步修复了 CI 分析报告中提到的两个潜在问题（git 浅克隆 + `|| true`、boost 包名错误）

## 潜在风险
- `rpm2cpio | cpio` 提取方式不会记录到 RPM 数据库，后续 `yum remove` 等命令无法管理这些文件，但在容器镜像构建场景中这是可接受的
- `uname -m` 依赖于构建节点的实际 CPU 架构，需要 CI 在对应架构的 runner 上构建
- 无
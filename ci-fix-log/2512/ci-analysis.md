# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM跨发行版依赖不兼容
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), is needed by, el9, aarch64.rpm

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 硬编码下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`——该 RPM 为 EL9（RHEL 9）构建，其 RPM 元数据声明的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖在 openEuler 的 glibc 打包中不被识别。同时 RPM 架构固定为 aarch64，与 CI 构建环境（x86_64，见 `#9` 中 meson 检测 `Host machine cpu: x86_64`）不匹配，即使依赖问题解决也会因架构错误而失败。

### 与 PR 变更的关联
该 Dockerfile 是本次 PR 新增文件（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，69 行新增）。FoundationDB RPM 安装步骤完全由此 PR 引入，失败与 PR 变更直接相关。

## 修复方向

### 方向 1（置信度: 高）
弃用 EL9 预编译 RPM，改为从 FoundationDB 源码编译安装，或使用 `rpm2cpio` 提取二进制文件后手动部署（绕过 RPM 依赖检查）。同时需处理架构适配：根据构建平台的 `$(uname -m)` 动态选择正确的 FoundationDB 二进制/源码。

### 方向 2（置信度: 中）
改用 `rpm -ivh --nodeps` 强制安装（openEuler 的 glibc 实际版本应满足 GLIBC_2.17 的 ABI 要求，仅是 RPM provides 标签不匹配），但仍需解决架构硬编码问题——aarch64 RPM 无法在 x86_64 上运行。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否提供 x86_64 架构的 RPM/二进制（当前只用了 aarch64 URL）
2. openEuler 24.03-LTS-SP3 的 glibc 实际版本和提供的 RPM capability 列表，确认 `--nodeps` 安装后 FoundationDB 客户端能否正常运行
3. FoundationDB 是否有官方源码构建指南，评估从源码编译的可行性及所需依赖
4. CI 构建矩阵的架构配置——确认 CI 是为 x86_64、aarch64 两台架构分别构建，还是仅单架构构建

## 修复验证要求
code-fixer 在修改 Dockerfile 后，必须：
1. 在 openEuler 24.03-LTS-SP3 容器内实际执行 FoundationDB 安装步骤，确认客户端二进制可正常运行
2. 验证 x86_64 和 aarch64 两个架构的 FoundationDB 下载 URL 均存在且对应正确架构
3. 若改用源码编译，确认编译产物 `fdbcli` 等二进制文件路径正确，后续 3FS cmake 步骤能正确找到 FoundationDB 头文件和库

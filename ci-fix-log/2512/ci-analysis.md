# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM跨发行版依赖不兼容
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_2.17)`, `foundationdb`, `el9`, `rpm -ivh`, `aarch64`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB RPM 是为 RHEL 9（`el9`）构建的，依赖 `libm.so.6(GLIBC_2.17)` 版本化符号，该符号在 openEuler 24.03-lts-sp3 的 glibc/libm 中不可用。此外，Dockerfile 中 RPM 下载 URL 硬编码了 `aarch64` 架构，而本次 CI 构建实际运行在 x86_64 架构上（日志 step #9 meson 输出 `Host machine cpu family: x86_64`），存在架构不匹配。

### 与 PR 变更的关联
PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 22-24 行的 FoundationDB 客户端 RPM 安装步骤直接导致了 CI 失败。这是 PR 引入的新代码，与该失败存在直接因果关系。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB 的 `el9` RPM 与 openEuler 发行版的 glibc ABI 不兼容。需要改用与 openEuler 24.03-lts-sp3 兼容的方式安装 FoundationDB 客户端。可考虑：
- 从 FoundationDB 官方容器镜像（`foundationdb/foundationdb:7.3.77`）中通过多阶段构建 `COPY --from` 提取 `fdbcli` 和相关库文件，而非安装 RPM
- 或通过源码编译 FoundationDB 客户端（`fdbclient`）来适配 openEuler 的运行时环境

### 方向 2（置信度: 高）
Dockerfile 中 FoundationDB RPM URL 硬编码为 `aarch64` 架构，未根据 `BUILDARCH` 做动态选择。即使 RPM 依赖兼容，在 x86_64 构建环境中安装 aarch64 RPM 也会失败。需根据 `TARGETARCH`/`BUILDARCH` 动态选择对应的 RPM 架构 URL（`x86_64` 或 `aarch64`）。FoundationDB 的 GitHub Releases 中同时提供 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`。

## 需要进一步确认的点
1. 在 openEuler 24.03-lts-sp3 容器中验证 FoundationDB 官方镜像的 `fdbcli` 二进制是否能直接运行（需检查动态链接库兼容性）
2. 确认 FoundationDB 7.3.77 的源码编译是否依赖 openEuler 仓库中缺失的 `-devel` 包
3. 验证 x86_64 架构下 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 openEuler 上是否也存在同样的 `libm.so.6(GLIBC_2.17)` 依赖问题

## 修复验证要求
code-fixer 在修改 Dockerfile 后，必须在 openEuler 24.03-lts-sp3 基础容器中逐 RUN 步骤执行验证（参考 oe-generator 规范 §6 "Mandatory Live Validation"），特别确认：
- FoundationDB 客户端安装步骤在所有目标架构（amd64 / arm64）上均无依赖错误
- `fdbcli --version` 能正常输出 FoundationDB 版本信息

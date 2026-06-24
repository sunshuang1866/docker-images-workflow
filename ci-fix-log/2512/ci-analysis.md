# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构不匹配的RPM下载
- 新模式症状关键词: Failed dependencies, libm.so.6, GLIBC_2.17, foundationdb-clients, aarch64, rpm -ivh, el9

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
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
ERROR: failed to solve: exit code: 1
Finished: FAILURE
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但本次 CI 构建运行在 x86_64 环境（日志中 rustup 报告 `default host triple is x86_64-unknown-linux-gnu`，meson 报告 `Host machine cpu family: x86_64`）。跨架构 RPM 的依赖声明（`libm.so.6(GLIBC_2.17)(64bit)`）在 openEuler x86_64 上无法被满足，rpm 安装失败。同时该 RPM 是为 RHEL/CentOS 9（`el9`）构建，与 openEuler 的 RPM 依赖声明体系存在兼容性差异。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，该文件第 22-24 行直接引入了本次失败的 RUN 步骤。未做架构自适应（如使用 `$(uname -m)` 动态选择 x86_64 或 aarch64 RPM URL），硬编码 `aarch64` 导致在 x86_64 CI 节点上必然失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中根据构建架构动态选择 FoundationDB RPM 的下载 URL。将硬编码的 `aarch64` 改为根据 `$(uname -m)` 输出映射正确的架构字符串（x86_64 → `x86_64`，aarch64 → `aarch64`），确保每个架构下载对应架构的 RPM。同时需验证 openEuler 上 `rpm -ivh` 直接安装 `el9` RPM 是否存在 glibc 版本兼容问题，若不兼容则需改用从源码编译或寻找 openEuler 原生 FoundationDB 包。

### 方向 2（置信度: 中）
放弃从 GitHub Releases 下载预编译 RPM，改为从 FoundationDB 官方 Docker 镜像或源码自行构建 FoundationDB 客户端库，以彻底避免跨发行版 RPM 兼容性问题。

## 需要进一步确认的点
1. FoundationDB `el9` RPM 在 openEuler 24.03 x86_64 上直接安装是否存在 glibc ABI 级兼容问题。需在 openEuler 24.03 容器内实际测试 `rpm -ivh` 安装 FoundationDB x86_64 RPM 是否能成功。
2. 历史知识库（模式18）记录了本 PR 之前的 CI 失败与 `git clone --depth 1` + commit hash checkout 不兼容相关，当前日志未到达 git clone 步骤（失败在步骤 5/9，git clone 在步骤 6/9），修复当前问题后可能会暴露该后续问题，建议一并排查。
3. `--depth 1` 浅克隆后 `git checkout ${VERSION}` 后跟 `|| true` 会静默失败，即使 RPM 问题修复，该步骤可能产生错误构建结果（checkout 失败但仍继续构建），需在修复后去除 `|| true` 并改用正确的浅克隆 checkout 方式。

## 修复验证要求
code-fixer 必须在修复 Dockerfile 后，分别在 x86_64 和 aarch64 的 openEuler 24.03-lts-sp3 容器中执行 `docker build` 验证：
1. FoundationDB RPM 安装步骤在两个架构下均能通过
2. 修复后的 git clone + checkout 步骤能正确 checkout 到指定 commit hash `22fca04`
3. 整体 Docker 镜像构建成功（10/10 步骤）

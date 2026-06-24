# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码错配
- 新模式症状关键词: `error: Failed dependencies`, `aarch64.rpm`, `GLIBC_2.17`, `x86_64`, `foundationdb`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，但 CI 构建环境为 `x86_64`（日志中 Rust 安装 tripple 为 `x86_64-unknown-linux-gnu`，fuse meson 检测到 `Host machine cpu: x86_64`），导致下载了错误架构的 RPM 包，`rpm -ivh` 因架构不匹配而失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全新文件，共 69 行），该 Dockerfile 的第 22-24 行包含 FoundationDB 客户端 RPM 安装步骤，URL 中架构字段写死为 `aarch64`，未根据构建环境的实际架构动态选择。此错误由本次 PR 的 Dockerfile 直接引入。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中 FoundationDB RPM 下载 URL 的架构字段从硬编码 `aarch64` 改为使用 BuildKit 内置变量 `${TARGETARCH}` 或通过 shell 条件判断动态选择 `x86_64` / `aarch64`。FoundationDB 7.3.77 同时提供 `x86_64` 和 `aarch64` 两种 RPM，需确保每种架构下载对应的包。

### 方向 2（置信度: 低）
即使架构正确，FoundationDB EL9 RPM 与 openEuler glibc 之间可能存在符号版本兼容性问题（`libm.so.6(GLIBC_2.17)` 依赖）。若修复架构后仍然失败，需考虑改用 FoundationDB 源码编译安装，或跳过 FoundationDB 客户端 RPM 安装步骤（如 3FS 可在无 FDB 客户端的情况下编译，运行时再挂载）。

## 需要进一步确认的点
1. 修复架构选择后，需验证 FoundationDB EL9 RPM 在 openEuler 24.03-LTS-SP3 上的 glibc 兼容性
2. 日志中断在步骤 [5/9]，后续步骤（3FS 源码 git clone + cmake 编译）尚未执行。知识库模式18 已标记本 PR 的 `git clone --depth 1` + commit hash checkout 存在不兼容风险，修复 FoundationDB 问题后可能出现新的构建错误
3. 知识库模式10 提及本 PR 中 `boost-foundation` 包名在 openEuler 中不存在，Dockerfile 第 10 行的 `yum install boost-devel` 后未单独安装 `boost-foundation`，需确认 yum install 阶段已解决此问题（日志显示 yum install 已成功，但需在修复后续步骤错误后重新验证整体构建）

## 修复验证要求
code-fixer 在提交前必须：
1. 从 FoundationDB GitHub Releases 确认 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 文件存在且可下载
2. 在 x86_64 openEuler 24.03-LTS-SP3 容器中手动执行 `rpm -ivh` 验证该 RPM 的 glibc 依赖可满足
3. 修复后重新触发完整 CI 构建，验证 3FS 编译步骤（步骤 6+）也能通过，特别是 git clone + cmake 编译阶段

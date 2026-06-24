# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: Failed dependencies, libm.so.6, aarch64, x86_64, architecture mismatch, foundationdb-clients, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

构建主机架构确凿证据：
- fuse3 meson 输出：`Host machine cpu family: x86_64`, `Host machine cpu: x86_64`
- Rust 工具链输出：`default host triple is x86_64-unknown-linux-gnu`

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB clients RPM 下载 URL 硬编码了 `aarch64` 架构，但当前 CI 构建运行在 x86_64 主机上。aarch64 RPM 包含的二进制文件依赖 aarch64 ABI 的 `libm.so.6`，在 x86_64 系统上无法满足该依赖关系，导致 `rpm -ivh` 失败。

### 与 PR 变更的关联
此次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（第 22-24 行为 FoundationDB RPM 安装步骤），该 Dockerfile 中的 RPM 下载 URL 直接写死了 `aarch64` 后缀，未根据 BUILDARCH/BUILDPLATFORM 等 BuildKit 变量进行架构自适应。这是 PR 引入的全新代码，与 PR 直接相关。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的 `aarch64` 替换为架构自适应变量。使用 BuildKit 预定义 ARG（如 `TARGETARCH`）或 shell 命令 `uname -m` 检测构建架构，构造正确的 RPM URL。FoundationDB 7.3.77 在 GitHub Releases 中同时提供了 `el9.x86_64.rpm` 和 `el9.aarch64.rpm`，只需替换架构部分即可。

### 方向 2（置信度: 低）
如果 FoundationDB 未提供对应架构的 RPM，可考虑从源码编译 FoundationDB clients 库。但这会大幅增加构建复杂度，且 FoundationDB 官方已提供 x86_64 RPM，方向 1 应优先采用。

## 需要进一步确认的点
- FoundationDB 7.3.77 的 GitHub Releases 中 x86_64 RPM 的准确文件名（预计为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）
- Dockerfile 中是否已声明 `ARG TARGETARCH` 以支持 BuildKit 架构变量
- `el9` 在 openEuler 24.03-LTS-SP3 上的兼容性 — RPM 以 `el9` 为目标构建，可能需要验证在 openEuler 上的实际兼容性（如果 x86_64 RPM 安装也出现依赖问题，需进一步处理）

## 修复验证要求
code-fixer 必须：
1. 在 x86_64 和 aarch64 两种架构的 CI 环境中验证 FoundationDB RPM 安装均通过
2. 确认 FoundationDB 7.3.77 的 GitHub Releases 页面确实存在 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`（通常在 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 页面 Assets 区域列出）
3. 如果 `el9` RPM 在 openEuler 上存在 glibc 版本兼容性问题，需改用 `el7` 版本的 RPM 或采用其他 client 库安装方式

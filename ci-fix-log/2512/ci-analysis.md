# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM跨发行版兼容性
- 新模式症状关键词: Failed dependencies, libm.so.6, GLIBC_2.17, foundationdb-clients, el9, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
------
Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码了 `aarch64` 架构和 `el9` 发行版标识。当前 CI 构建环境为 x86_64（日志中 meson 检测到 `Host machine cpu family: x86_64`，rustup 安装 `x86_64-unknown-linux-gnu` toolchain），下载的 aarch64 RPM 依赖 `libm.so.6(GLIBC_2.17)(64bit)` 在 openEuler 24.03 中无法满足，rpm 安装失败。

### 与 PR 变更的关联
PR 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，所有 69 行均为新增内容。该错误是 PR 引入的 Dockerfile 中 FoundationDB 安装步骤的硬编码 URL 缺陷直接导致。PR 还包含大量 `.agents/` → `.claude/` 目录重命名和代理规范更新，但这些与构建失败无关。

## 修复方向

### 方向 1（置信度: 高）
**架构感知的 RPM URL + 发行版兼容性处理**。FoundationDB 上游同时提供 amd64 和 arm64 的 RPM，需根据实际构建架构（通过 BuildKit 的 `TARGETARCH` ARG 或 shell `uname -m` 判断）动态选择正确的 RPM URL。同时需验证 `el9` RPM 在 openEuler 24.03 上的实际兼容性——若 glibc 版本符号仍然不匹配，需考虑从 FoundationDB 源码编译客户端库，或使用多阶段构建从 FoundationDB 官方 Docker 镜像中 COPY 二进制文件。

### 方向 2（置信度: 中）
**绕过 RPM 安装，改用 FoundationDB 官方容器镜像提取客户端库**。FoundationDB 官方发布 Docker 镜像，可采用多阶段构建从其镜像中 `COPY` 所需的客户端库和头文件，避免 RPM 发行版兼容性问题。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 `el9.x86_64.rpm` 在 openEuler 24.03 上是否也存在 `GLIBC_2.17` 依赖缺失——需在 openEuler 24.03 容器中实际测试 `rpm -ivh` 验证兼容性
2. FoundationDB 是否提供不依赖特定 glibc 版本的静态链接客户端库或源码构建方式
3. 3FS 项目构建时对 FoundationDB 客户端的具体链接需求（头文件路径、库文件名称），以确定多阶段构建 COPY 的可行性
4. 除 FoundationDB 安装失败外，`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 中还存在以下潜在问题（当前构建未到达这些步骤，但修复后可能暴露）：
   - `git clone --depth 1` 浅克隆与 `git checkout ${VERSION} 2>/dev/null || true` 组合使用时，`|| true` 会静默掩盖 checkout 失败（参考 模式18）
   - `yum install` 中的 `boost-devel` 是否能覆盖 `boost-foundation` 等运行时包需求（参考 模式10 历史记录中同一 PR 的关联记录）

## 修复验证要求
1. code-fixer 必须分别在 amd64 和 arm64 的 openEuler 24.03 容器中验证 FoundationDB 客户端的安装方式，确保所选方案在两个架构上均能成功安装
2. 如采用 RPM 方式，code-fixer 必须从 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 确认对应架构的 RPM 文件名是否确实存在，并在容器中执行 `rpm -ivh` 通过后再提交
3. 如改为多阶段构建 COPY 方式，code-fixer 必须验证从 `foundationdb/foundationdb:7.3.77` 镜像中复制的库文件在 openEuler 容器中能正常链接

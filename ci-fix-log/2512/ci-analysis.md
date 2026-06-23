# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: Failed dependencies, libm.so.6(GLIBC_x.y), el9.aarch64, foundationdb, Architecture mismatch

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22-24
```

### 根因定位
- 失败位置: Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码了 `aarch64` 架构和 `el9` 发行版标识。CI 构建环境（x86_64）中，openEuler 的 glibc 包无法满足该 `el9.aarch64` RPM 的依赖声明 `libm.so.6(GLIBC_2.17)(64bit)`，导致 `rpm -ivh` 依赖检查失败。

### 与 PR 变更的关联
PR 变更直接引入了该 Dockerfile（全新文件，69 行 added）。Dockerfile 第 22-24 行的 FoundationDB RPM 安装步骤为此 PR 首次添加，是本次 CI 失败的直接触发变更。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端 RPM 的下载 URL 改为**架构自适应**，根据构建平台选择对应的 RPM 文件名：
- x86_64 构建时下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64 构建时下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

同时需验证 x86_64 版 RPM 在 openEuler x86_64 容器内的依赖是否满足（`libm.so.6(GLIBC_2.17)(64bit)` 等）。若 el9 RPM 与 openEuler 的 glibc 依赖声明仍然不兼容，需考虑备选方案。

### 方向 2（置信度: 中）
若 el9 RPM 在两个架构上都与 openEuler 依赖不兼容，改用 `--nodeps --ignorearch` 强制安装 RPM（前提是运行时 `libm.so.6` 实际存在且 ABI 兼容），或从 FoundationDB 源码构建客户端库。

### 方向 3（置信度: 低）
放弃 RPM 安装方式，改为下载 FoundationDB 官方 Docker 镜像并从中 `COPY` 客户端二进制文件（参考模式16的多阶段构建方案）。

## 需要进一步确认的点
1. **构建达到后还有更多失败**：当前构建在步骤 #10（Dockerfile 第 5/9 步）就失败了，无法得知后续步骤是否能通过。已知该 Dockerfile 存在以下潜在问题（参考历史模式）：
   - **模式18**：`git clone --depth 1` 后 `git checkout ${VERSION} 2>/dev/null || true` 静默掩盖了浅克隆无法 checkout 历史 commit hash 的问题（Dockerfile 第 27-29 行）。runtime 层的 `yum install boost-foundation` 包名可能不存在于 openEuler 仓库。
2. **el9 RPM 与 openEuler 兼容性**：FoundationDB 仅发布 `el7`/`el9`（RHEL/CentOS）架构的 RPM，需要在实际 openEuler 容器中验证 `x86_64` 变体的依赖是否满足。`libm.so.6(GLIBC_2.17)(64bit)` 理论上应被 openEuler 的 glibc 提供，但错误表明实际未匹配，可能是 RPM 依赖声明与 openEuler glibc 包的 provides 字段不兼容。
3. **rustup 工具链架构**：rustup 安装了 `x86_64-unknown-linux-gnu` 工具链，但 3FS 项目 README 声明支持 `amd64, arm64`。若目标是双架构构建，Dockerfile 需处理架构相关逻辑（FoundationDB RPM、rust 工具链目标三元组等）。

## 修复验证要求
1. **code-fixer 必须在 openEuler x86_64 容器中验证**：使用 `docker run --rm openeuler/openeuler:24.03-lts-sp3` 启动容器，在容器内下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 并执行 `rpm -ivh` 确认依赖满足。
2. **修复 FoundationDB RPM 后，必须持续跟进到步骤 #11（3FS 编译步骤）**：确认后续的 git clone/cmake 构建不会因模式18（git 浅克隆 + commit hash）或其他问题再次失败。
3. **arm64 架构构建需单独验证**：PR README 声明支持 `arm64`，修复方案需覆盖 aarch64 路径（原有 URL 在 aarch64 构建时应继续工作，但不能硬编码架构）。

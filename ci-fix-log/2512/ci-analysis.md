# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码
- 新模式症状关键词: Failed dependencies, foundationdb-clients, aarch64, rpm -ivh, GLIBC_2.17

## 根因分析

### 直接错误
```
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
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
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:22-24
- 失败原因: FoundationDB RPM URL 硬编码了 `aarch64` 架构，但 CI 构建主机为 x86_64（日志 #9 中 meson 明确输出 `Host machine cpu: x86_64`，rustup 安装 `x86_64-unknown-linux-gnu`）。`rpm -ivh` 安装 aarch64 架构的 RPM 包时，依赖求解器检测到该包的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖无法由 x86_64 系统上的 glibc 满足，导致安装失败。

### 与 PR 变更的关联
PR 新增了整个 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行全新增），FoundationDB RPM 安装步骤是该 Dockerfile 中的第 5 个 RUN 步骤。该硬编码问题仅在 x86_64 构建环境中暴露——Dockerfile 作者可能在 aarch64 环境下编写并测试，未验证 x86_64 架构兼容性。此外，Dockerfile 中其他位置也存在架构硬编码（如 clang library 路径：`aarch64-openEuler-linux-gnu`、`libclang_rt.builtins-aarch64.a`）。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB RPM URL 应根据构建架构动态选择。FoundationDB 同时提供了 x86_64 和 aarch64 的 RPM 包：
- x86_64: `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64: `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

修复思路：在 Dockerfile 中利用 BuildKit 内置 `TARGETARCH` 变量或通过 shell 条件判断，动态构造正确的 RPM 下载 URL。

### 方向 2（置信度: 高 — 与方向1需同步处理）
Dockerfile 中 clang library 符号链接路径也硬编码了 aarch64：
```
ln -sf /usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/...
```
x86_64 上的对应路径为 `/usr/lib/clang/17/lib/x86_64-openEuler-linux-gnu/...`。需与方向 1 一并按架构动态选择正确路径。

### 方向 3（置信度: 中 — 当前构建未到达此步骤，但修复方向1后可能暴露）
历史模式 18 指出该 Dockerfile 的 `git clone --depth 1` + `git checkout ${VERSION}` 组合存在浅克隆与 commit hash checkout 不兼容问题（`2>/dev/null || true` 静默掩盖错误）。若 CI 当前使用的是 x86_64 builder，修复方向 1 后构建将继续推进到该 git clone 步骤，可能触发此潜在问题。建议一并修复。

## 需要进一步确认的点
1. 确认 FoundationDB 7.3.77 的 x86_64 RPM 在 openEuler 24.03-LTS-SP3 x86_64 容器中是否确实可安装（`rpm -ivh` 依赖检查通过）。
2. 确认 openEuler 24.03-LTS-SP3 x86_64 容器中 clang-17 的库文件路径是否为 `/usr/lib/clang/17/lib/x86_64-openEuler-linux-gnu/`。
3. 确认 `boost-foundation` 包名在 openEuler 24.03-LTS-SP3 yum 仓库中是否存在（历史模式 10 提到该包名可能不存在，但当前构建未推进到该 RUN 步骤，无法从日志验证）。

## 修复验证要求
1. code-fixer 必须在 x86_64 环境中验证修复后的 Dockerfile 能否完整通过 `docker build`。
2. code-fixer 必须从 FoundationDB GitHub releases 页面确认 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 文件确实存在且可下载。
3. 修复方向 1 生效后，若构建继续失败，需重新分析后续步骤（特别是 git clone 和 cmake 阶段）的错误日志。

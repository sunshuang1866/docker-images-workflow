# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨架构RPM依赖失败
- 新模式症状关键词: error: Failed dependencies, libm.so.6, foundationdb-clients, aarch64, el9, rpm -ivh, GLIBC_2.17

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |
--------------------
ERROR: failed to solve: process "..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码了 `aarch64` 架构后缀。当前 CI 构建在 `x86_64` 环境上执行（日志 #9 meson 输出确认为 `Host machine cpu family: x86_64`），RPM 安装 aarch64 架构的包时，要求系统中存在 aarch64 架构的依赖库提供者，但 x86_64 容器镜像中只有 x86_64 架构的 glibc（提供 `libm.so.6(GLIBC_2.17)(64bit)` 为 x86_64 而非 aarch64），导致依赖解析失败。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全部 69 行为新增）。该 Dockerfile 在第 22 行硬编码了 aarch64 架构的 FoundationDB RPM URL。CI 流水线需要同时构建 x86_64 和 aarch64 两种架构的镜像，该 URL 在 x86_64 构建时不匹配，导致构建失败。**此失败由本次 PR 直接引入**。

## 潜在后续失败点

修复当前 FoundationDB RPM 架构错误后，Dockerfile 中还存在以下硬编码/兼容性问题，会在后续构建步骤中暴露：

| 行号 | 问题 | 严重程度 |
|------|------|----------|
| 37-42 | Clang 库路径硬编码 `aarch64-openEuler-linux-gnu`，x86_64 上该路径不存在（应为 `x86_64-openEuler-linux-gnu`） | 高 |
| 27-29 | `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null \|\| true`，commit hash 不在浅克隆范围内会静默失败（历史模式18） | 中 |
| 54 | `boost-foundation` 包名在 openEuler 24.03-LTS-SP3 yum 仓库中可能不存在（历史模式10 标注为 PR #2512 已知问题） | 中 |

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构标识从硬编码 `aarch64` 改为动态检测。FoundationDB 7.3.77 GitHub Releases 页面同时提供了 `x86_64` 和 `aarch64` 两种架构的 RPM 包。使用 BuildKit 的 `TARGETARCH` ARG 或 shell 命令 `uname -m` 动态选择正确的 RPM 架构后缀（x86_64 对应 `x86_64`，aarch64 对应 `aarch64`），使同一 Dockerfile 同时支持两种架构构建。

### 方向 2（置信度: 中，需同步修复的关联问题）
修复 Clang 库符号链接部分的架构硬编码（第 37-42 行）。当前路径 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/` 仅存在于 aarch64 镜像中，x86_64 的对应路径为 `/usr/lib/clang/17/lib/x86_64-openEuler-linux-gnu/`。需与方向 1 使用相同的架构检测逻辑，避免修复 FoundationDB 后立即在 Clang 阶段再次失败。

### 方向 3（置信度: 高，git clone 问题）
将第 27-29 行的 git 操作从 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true` 改为先完整 clone 再 checkout，或先 `git fetch origin ${VERSION}` 再 checkout。当前写法在 commit hash 为浅克隆不可达时静默失败，导致使用错误的代码版本进行编译。

## 需要进一步确认的点
1. FoundationDB 7.3.77 在 GitHub Releases 上是否有 `x86_64` 架构的 RPM（需验证 URL `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 可下载）
2. openEuler 24.03-LTS-SP3 镜像中的 `clang` 包在 x86_64 架构上，lib/clang/17/lib 下的实际目录名是否为 `x86_64-openEuler-linux-gnu`
3. `boost-foundation` 是否为 openEuler 24.03-LTS-SP3 yum 仓库中的有效包名，或需替换为 `boost-devel`
4. 建议获取 aarch64 架构构建的 CI 日志，确认当前 Dockerfile 在 aarch64 环境下是否还有其他问题

## 修复验证要求
修复后必须在 **x86_64 和 aarch64 两种架构**的 CI 环境中分别验证构建通过：
1. x86_64 构建需验证 FoundationDB RPM URL 的架构检测逻辑正确，且 RPM 依赖可正常解析
2. x86_64 构建需验证 Clang 库路径的架构检测逻辑正确
3. 两种架构均需验证 `git checkout` 在给定 commit hash `22fca04` 下能否正确切换到目标版本
4. 两种架构均需验证 `yum install boost-foundation` 是否成功，若失败则需确认正确的包名

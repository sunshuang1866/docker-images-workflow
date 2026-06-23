# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构特定URL硬编码
- 新模式症状关键词: aarch64, x86_64, foundationdb, Failed dependencies, rpm, architecture mismatch, libm.so.6

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
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
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 的下载 URL 硬编码为 `aarch64` 架构，而 CI 构建环境实际架构为 x86_64（日志中 meson 检测 `Host machine cpu family: x86_64`，Rust 默认 target `x86_64-unknown-linux-gnu`），导致无法安装该 RPM。

### 与 PR 变更的关联
该 Dockerfile 是本次 PR 新增的文件（diff 中 `new_file: True`），架构特定的 RPM URL 硬编码问题由 PR 直接引入。此外，Dockerfile 中还包含其他 aarch64 专属路径（如 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/`），这些在 x86_64 构建中同样不正确。README 声明该镜像支持 amd64 和 arm64，但 Dockerfile 实际仅对 aarch64 进行适配。

### 潜在连锁问题
除当前失败点外，该 Dockerfile 还存在以下已确认的潜伏问题（本次构建尚未执行到）：
- **知识库模式18**：`git clone --depth 1` 浅克隆后 `git checkout ${VERSION}`（commit hash `22fca04`）无法检出，且 `2>/dev/null || true` 静默掩盖了错误，导致实际构建了错误的代码版本。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 的下载 URL 从硬编码 `aarch64` 改为基于 `TARGETARCH`（BuildKit 内置 ARG）或 `$(uname -m)` 动态构造，使 x86_64 构建下载 `x86_64` RPM，aarch64 构建下载 `aarch64` RPM。同时，Dockerfile 中其他 aarch64 硬编码路径（clang 库符号链接路径 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/`）也需对应架构感知化处理。

### 方向 2（置信度: 中）
考虑 FoundationDB 7.3.77 提供的 `el9` RPM 是否与 openEuler 24.03 LTS SP3（基于 openEuler 24.03）兼容。openEuler 的基础镜像与 RHEL/CentOS 并不共享相同的 glibc 版本符号体系，使用 `el9` 类 RPM 可能存在版本符号不匹配的隐患。可考虑从 FoundationDB 官方 Docker 镜像中 `COPY` 二进制文件替代 RPM 安装（类似模式16）。

### 方向 3（置信度: 高 — 潜伏问题）
修复 `git clone --depth 1` 与 commit hash checkout 的兼容性问题（模式18）：去掉 `--depth 1` 做完整克隆，或将 checkout 逻辑改为先 `git fetch origin ${VERSION}` 再 `git checkout ${VERSION}`，并移除掩盖错误的 `2>/dev/null || true`，让 checkout 失败时构建明确报错。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否提供 `el9.x86_64` 版本的 RPM（即 URL `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 是否有效）。
2. openEuler 24.03 LTS SP3 的 glibc 版本是否满足 FoundationDB 7.3.77 RPM 的依赖（`GLIBC_2.17` 等版本符号）。
3. `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 第 42-47 行的 clang 库符号链接路径是否需要 X86_64 对应的路径（`x86_64-openEuler-linux-gnu`）替代 `aarch64-openEuler-linux-gnu`。
4. 上游仓库 `deepseek-ai/3fs` 的 commit `22fca04` 是否确实存在于默认分支历史中（验证 git checkout 目标的正确性）。

## 修复验证要求
- 修复后需在 x86_64 和 aarch64 两个架构的 CI 环境中分别验证构建通过。
- 验证 `foundationdb-clients` RPM 的架构选择逻辑正确后，需确认 `fdbcli`、`libfdb_c.so` 等 FoundationDB 客户端二进制能正常工作。
- 若修复方向包含 git clone 深度调整，需确认 commit `22fca04` 能被正确检出且构建产物与预期一致。

# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码致RPM依赖失败
- 新模式症状关键词: error: Failed dependencies, libm.so.6, foundationdb-clients, aarch64, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构标识，而 CI 构建环境运行在 x86_64 上（证据：rustup 安装 `x86_64-unknown-linux-gnu` toolchain、fuse meson 检测到 `Host machine cpu family: x86_64`）。x86_64 系统无法满足 aarch64 RPM 的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖，导致 `rpm -ivh` 失败。

### 与 PR 变更的关联
该 Dockerfile 为本 PR 全新增文件（69 行新增），其中 FoundationDB RPM URL 硬编码了 `aarch64` 架构，直接导致 x86_64 CI 环境构建失败。PR 变更与失败 100% 相关。

### 后续阻塞点（当前日志未触发，但必将触发）
以下问题存在于同一 Dockerfile 中，修复当前错误后会依次暴露：

1. **Clang 库路径硬编码 aarch64**（Dockerfile 约第 40-44 行）：`ln -sf /usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/...` 路径在 x86_64 上不存在（应为 `x86_64-openEuler-linux-gnu`）。
2. **git 浅克隆与 commit hash checkout 冲突**（模式18）：`git clone --depth 1` 后 `git checkout ${VERSION}` 对历史 commit hash 无效，且 `2>/dev/null || true` 静默掩盖了错误。
3. **ENV 自引用未定义变量**（模式20 同类）：`ENV LD_LIBRARY_PATH=/opt/3fs/lib:/usr/local/lib` 未自引用，但存在潜在风险。本次日志因提前失败未触发。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM URL 中的 `aarch64` 改为动态架构检测。FoundationDB 为 x86_64 提供的包名为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`。需在 `RUN` 中通过 `uname -m` 检测实际架构（注意 openEuler x86_64 上 `uname -m` 返回 `x86_64`，与 URL 中 `x86_64` 一致），构造正确的 RPM URL。

### 方向 2（置信度: 高）
连同 Clang 库路径中的硬编码 `aarch64` 一并修复：将 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu` 改为通过通配符或 `uname -m` 动态生成对应架构路径。

## 需要进一步确认的点
1. FoundationDB 7.3.77 在 openEuler 24.03-LTS-SP3 上通过 RPM 安装后是否需要额外运行时依赖（`libm` 依赖之外的库），需在修复后的构建日志中验证。
2. FoundationDB GitHub releases 页面中 x86_64 RPM 的确切文件名格式（是否包含 `.el9`、版本号格式），建议在修复时直接从 releases API 获取或手动确认 URL。
3. 模式18（git 浅克隆 + commit hash）修复后，需确认 `git fetch origin ${VERSION}` 能否在 shallow clone 中成功拉取指定 commit。

## 修复验证要求
1. code-fixer 必须验证 FoundationDB 7.3.77 在 openEuler 24.03-LTS-SP3 x86_64 容器中通过 RPM 安装后，`fdbcli` 或其他客户端二进制文件可正常执行。
2. 修复后需在 x86_64 和 aarch64 两个架构的 CI 环境中分别验证构建通过。
3. 若同时修复了 Dockerfile 中 git checkout 逻辑（模式18），需验证 `git -C /tmp/3fs checkout 22fca04` 能正确签出指定 commit。

# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM URL
- 新模式症状关键词: error: Failed dependencies, foundationdb-clients, el9.aarch64.rpm, libm.so.6(GLIBC_2.17)

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构，而当前 CI 构建运行在 x86_64 主机上（见步骤 #8 安装 `x86_64-unknown-linux-gnu` Rust 工具链、步骤 #9 meson 检测 `Host machine cpu: x86_64`）。跨架构 RPM 安装导致依赖解析失败（`libm.so.6(GLIBC_2.17)(64bit)` 在 x86_64 系统上不满足 aarch64 RPM 的依赖要求）。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 22-24 行硬编码了 FoundationDB 的 aarch64 RPM URL。该 Dockerfile 需要在多架构 CI 构建（x86_64 和 aarch64）中均通过，但当前仅对 aarch64 测试环境有效，x86_64 构建必然失败。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构标识从硬编码 `aarch64` 改为 BuildKit 内置变量（如 `TARGETARCH`），使其能根据目标构建架构自动选择正确的 RPM 包。FoundationDB 同时发布 x86_64 和 aarch64 的 el9 RPM，对应文件名分别为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，需在 URL 中动态替换架构字段。

### 方向 2（置信度: 高）
Dockerfile 中还存在其他架构硬编码问题（第 5 个 RUN 中的 clang runtime 库路径硬编码 `aarch64-openEuler-linux-gnu`），修复 FoundationDB 步骤后，x86_64 构建会继续推进到 cmake 编译步骤，届时 clang runtime 库的架构路径硬编码也需要同步修复——同样使用 `TARGETARCH` 将 `aarch64` 替换为运行时架构。

### 方向 3（置信度: 高，历史模式 18）
Dockerfile 中 `git clone --depth 1 --shallow-submodules` 后使用 `git checkout ${VERSION} 2>/dev/null || true` 尝试 checkout 指定 commit hash `22fca04`，该方法与浅克隆不兼容（浅克隆不含历史 commit），且 `|| true` 静默掩盖了 checkout 失败。此问题在 knowledge base 的 **模式18** 中已记录为 PR #2512 的已知问题，若修复方向 1 和 2 后 x86_64 构建能推进到这一步，此问题同样会暴露。应将 checkout 逻辑改为先 `git fetch origin ${VERSION}` 再 `git checkout FETCH_HEAD`。

## 需要进一步确认的点
1. FoundationDB 7.3.77 在 GitHub Releases 中的 x86_64 RPM 文件名确认为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`（需访问 FoundationDB releases 页面确认）。
2. openEuler 24.03-lts-sp3 x86_64 镜像中 clang-17 runtime 库的实际路径（推测为 `/usr/lib/clang/17/lib/x86_64-openEuler-linux-gnu/`），需在 openEuler 24.03-lts-sp3 x86_64 容器中验证。
3. `git clone --depth 1` + commit hash checkout 的修复建议（方向 3）在 knowledge base 模式 18 中已有验证，可直接套用。

## 修复验证要求
- code-fixer 必须验证 FoundationDB 7.3.77 同时在 x86_64 和 aarch64 的 openEuler 24.03-lts-sp3 容器中能成功安装（`rpm -ivh` 通过且无依赖错误）。
- 修复 clang 路径后，必须在 x86_64 容器中验证 `cmake -S /tmp/3fs -B /tmp/3fs/build -DCMAKE_CXX_COMPILER=/usr/bin/clang++ ...` 能成功配置（不需要完整编译，确保 cmake 配置阶段不再因 clang runtime 库缺失而失败即可）。
- 修复 git checkout 逻辑后，必须在构建日志中确认实际 checkout 到 commit `22fca04` 而非默认分支 HEAD。

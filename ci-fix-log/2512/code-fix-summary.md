# 修复摘要

## 修复的问题
Dockerfile 中三处架构硬编码导致 x86_64 CI 构建失败：FoundationDB RPM URL 硬编码 aarch64、clang runtime 库路径硬编码 aarch64、git clone 浅克隆与 commit hash checkout 不兼容。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 三处修复

### 修复 1：FoundationDB 安装（方向 1）
- **原代码**: 硬编码 `https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 直接下载 aarch64 RPM 并安装
- **修复**: 改用多阶段构建 `FROM foundationdb/foundationdb:7.3.77 AS fdb` + `COPY --from=fdb` 从官方多架构镜像复制二进制文件，同时增加 `fdb-headers` 下载用于 3fs 编译
- **验证**: 已从 Docker Hub 确认 `foundationdb/foundationdb:7.3.77` 同时支持 `amd64` 和 `arm64` 架构；已从 GitHub Releases 确认 `fdb-headers-7.3.77.tar.gz` 可访问（HTTP 302→200）

### 修复 2：clang runtime 库路径（方向 2）
- **原代码**: 硬编码 `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/`
- **修复**: 使用 `ARCH=$(uname -m)` 运行时检测架构，路径替换为 `/usr/lib/clang/17/lib/${ARCH}-openEuler-linux-gnu/`，同时 symlink 目标也动态使用 `${ARCH}`

### 修复 3：git clone 与 checkout（方向 3）
- **原代码**: `git clone --recurse-submodules --depth 1 --shallow-submodules ...` 后跟 `git checkout ${VERSION} 2>/dev/null || true`（浅克隆不含历史 commit，checkout 静默失败）
- **修复**: 改为 `git clone --recurse-submodules ...`（完整克隆），移除 `|| true` 使 checkout 失败能正确传播，移除 submodule update 中的 `--depth 1`

## 修复逻辑
CI 失败根因是 PR #2512 原始代码中 Dockerfile 的三处架构硬编码：

1. **FoundationDB RPM URL 硬编码 aarch64**：CI x86_64 构建时下载 aarch64 RPM，导致依赖解析失败（`libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64`）。修复方案从 RPM 安装切换为多阶段 Docker 构建，利用 Docker 原生的多架构镜像选择能力，无需手动处理架构分支。

2. **clang runtime 路径硬编码 aarch64**：即使 FoundationDB 修复后构建继续推进，clang 编译步骤也会因找不到 x86_64 架构的 runtime 库而失败。修复使用 `uname -m` 运行时动态获取架构标识。

3. **浅克隆 + commit hash checkout**：`--depth 1` 浅克隆不包含历史 commit，`git checkout ${VERSION}` 必然失败，但被 `|| true` 静默掩盖。修复使用完整克隆并移除错误掩盖。

## 潜在风险
- **FoundationDB 镜像可用性**：`FROM foundationdb/foundationdb:7.3.77` 依赖 Docker Hub 可用性，但已确认该 tag 同时有 amd64/arm64 镜像，风险极低。
- **`uname -m` 与容器化构建**：`ARCH=$(uname -m)` 在 Docker 构建中返回容器内架构（与目标架构一致），适用于本项目的 native/emulated 构建环境。若未来引入纯交叉编译场景才需要改用 BuildKit `TARGETARCH`。
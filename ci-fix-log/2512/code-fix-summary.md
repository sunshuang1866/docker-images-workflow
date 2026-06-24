# 修复摘要

## 修复的问题
3FS Dockerfile 中 FoundationDB RPM 下载 URL 和 Clang 库路径硬编码 `aarch64` 架构，导致在 x86_64 CI 环境构建失败。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 将 FoundationDB 安装从 aarch64 RPM 硬编码改为多阶段构建方式，并将 Clang 库路径从硬编码 aarch64 改为运行时动态检测

## 修复逻辑
CI 分析报告指出的三个架构硬编码问题均已修复，对应关系如下：

1. **FoundationDB RPM URL 硬编码 aarch64** (原 Dockerfile 第 22-24 行)：删除 `curl ... foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh ...`，改为多阶段构建方案：
   - 新增 `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb` 多阶段构建层，利用该 Docker 官方镜像的多架构清单（manifest list）自动匹配构建平台架构
   - 通过 `COPY --from=fdb` 获取 `fdbcli` 和 `libfdb_c.so`，避免直接下载单架构 RPM
   - FDB headers 下载 URL 不含架构后缀，无需修改

2. **Clang 库路径硬编码 `aarch64-openEuler-linux-gnu`** (原 Dockerfile 第 28-29 行)：改为 `ARCH=$(uname -m) && ... /usr/lib/clang/17/lib/${ARCH}-openEuler-linux-gnu/...`，在容器内运行时动态检测 CPU 架构（x86_64 上 `uname -m` 返回 `x86_64`，aarch64 上返回 `aarch64`）

3. **静态库目标名硬编码 `libclang_rt.builtins-aarch64.a`** (原 Dockerfile 第 30 行)：改为 `.../libclang_rt.builtins.a /usr/lib64/clang/17/lib/linux/libclang_rt.builtins-${ARCH}.a`，目标路径也使用动态架构变量

验证结果：
- FoundationDB 7.3.77 Docker 镜像已确认在 Docker Hub 上存在（HTTP 200），支持多架构清单
- FoundationDB x86_64 RPM 单独下载 URL 返回 404，但修复采用多阶段构建方式已完全绕过此问题
- openEuler 24.03-LTS-SP3 上 Clang 17 的库目录结构在 x86_64 下预期路径为 `/usr/lib/clang/17/lib/x86_64-openEuler-linux-gnu/`，由 `uname -m` 返回的 `x86_64` 正确拼接

## 潜在风险
- 多阶段构建中的 `COPY --from=fdb` 依赖 foundationdb/foundationdb 镜像内文件路径（`/usr/bin/fdbcli`、`/usr/lib/libfdb_c.so`）在所有架构的镜像中保持一致，已从该镜像的官方文档确认路径有效
- `ARCH=$(uname -m)` 在 QEMU 用户模式模拟的跨平台构建场景下，若 QEMU/binfmt_misc 未正确截获 `uname()` 系统调用，可能返回宿主机架构而非容器目标架构，导致 Clang 库路径不匹配。但 openEuler CI 当前为原生架构构建，此风险在当前场景不触发
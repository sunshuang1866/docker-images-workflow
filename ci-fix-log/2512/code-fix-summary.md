# 修复摘要

## 修复的问题
Dockerfile 中 FoundationDB 客户端安装方式在 x86_64 架构 CI 环境构建失败——原 RPM 下载 URL 硬编码为 aarch64 架构，导致 rpm -ivh 失败（libm.so.6(GLIBC_2.17) 依赖不满足）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 以多阶段构建（COPY --from=fdb）替代 FoundationDB RPM 安装；移除浅克隆 `--depth 1` 参数和 `|| true` 错误掩盖；移除不存在的 `boost-foundation` 包名；添加 `libevent-devel` 构建依赖、FDB headers 下载、clang 多架构符号链接处理。

## 修复逻辑

### 根因修复：FoundationDB 客户端架构硬编码
原始 PR 使用 `rpm -ivh` 安装 FoundationDB 客户端 RPM，URL 中硬编码了 `aarch64`，在 x86_64 CI 构建机上失败。CI 分析建议使用 Docker BuildKit `TARGETARCH` 变量做架构映射。

实际采用的修复方案（已在 fix 分支上提交）更优：使用 Docker 多阶段构建，通过 `FROM foundationdb/foundationdb:7.3.77 AS fdb` 引用官方 FoundationDB 镜像，然后 `COPY --from=fdb /usr/bin/fdbcli` 和 `COPY --from=fdb /usr/lib/libfdb_c.so` 获取客户端二进制。已验证：
- `foundationdb/foundationdb:7.3.77` 在 Docker Hub 上同时支持 amd64 和 arm64 架构
- 官方 FoundationDB Dockerfile (packaging/docker/Dockerfile@7.3.77) 确认 `/usr/bin/fdbcli` 和 `/usr/lib/libfdb_c.so` 路径存在
- `fdb-headers-7.3.77.tar.gz` 下载 URL 已验证可用（HTTP 302 重定向至实际文件）

### 附带修复（历史知识库模式18、模式10）
- **浅克隆问题（模式18）**：移除 `git clone --depth 1` 和 `|| true` 错误掩盖，改为完整克隆，确保 `git checkout ${VERSION}` 和 `./patches/apply.sh` 能正确执行
- **包名错误（模式10）**：移除运行时 yum install 中的 `boost-foundation` 包名
- **构建依赖**：添加 `libevent-devel` 到构建阶段 yum install
- **多架构支持**：添加 clang 符号链接的 `ARCH=$(uname -m)` 动态检测

## 潜在风险
- 多阶段构建引入了对 `foundationdb/foundationdb:7.3.77` 镜像的依赖，若 Docker Hub 不可达或该镜像被移除，构建将失败。替代方案为 CI 分析方向 1（使用 TARGETARCH 变量动态选择 RPM URL）。
- 当前构建只验证到步骤 5/9，后续步骤（git clone + cmake 编译、yum remove、运行时 yum install）尚未在 CI 上验证通过，修复后需完整 CI 运行确认。
# 修复摘要

## 修复的问题
CI 构建失败的两个根因已在当前 `fix/2512` 分支中完成修复：FoundationDB RPM 平台不兼容（方向1）和 git shallow clone 导致 checkout 失败被掩盖（方向3）。

## 修改的文件
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 无需进一步修改，修复已通过此前提交完成。

## 修复逻辑

### 方向1（FoundationDB RPM → 多阶段构建）
- 根因：原 Dockerfile 使用 `curl ... foundationdb-clients-*.el9.aarch64.rpm && rpm -ivh` 安装 FoundationDB 客户端，该 RPM 依赖 `libm.so.6(GLIBC_2.17)` 版本化符号，openEuler 24.03-LTS-SP3 的 glibc 不提供此符号，导致 `rpm -ivh` 依赖检查失败。
- 修复方式：改为多阶段构建 —— `FROM foundationdb/foundationdb:${FDB_VERSION} AS fdb`（第4行），通过 `COPY --from=fdb /usr/bin/fdbcli /usr/bin/fdbcli`（第26行）和 `COPY --from=fdb /usr/lib/libfdb_c.so /usr/lib64/libfdb_c.so`（第27行）直接提取二进制，跳过 RPM 包管理器的依赖检查。FoundationDB Headers 通过 GitHub Release tar.gz 下载（第29行），该方式不涉及平台依赖。
- 验证：已通过 Docker Hub Registry API 确认 `foundationdb/foundationdb:7.3.77` 镜像同时支持 `amd64` 和 `arm64` 架构，因此在 aarch64 CI 环境中可正常拉取。

### 方向3（shallow clone + checkout 修复）
- 根因：原 Dockerfile 使用 `git clone --recurse-submodules --depth 1 --shallow-submodules` 进行浅克隆，随后 `git checkout ${VERSION} 2>/dev/null || true` 无法在浅克隆中 checkout 指定 commit hash（`VERSION=22fca04`），`|| true` 掩盖了失败。
- 修复方式：移除 `--depth 1` 和 `--shallow-submodules` 参数，改为完整克隆（第35行）；移除 `2>/dev/null || true` 错误掩盖，改为 `git -C /tmp/3fs checkout ${VERSION} &&`（第36行）使 checkout 失败时构建正确中断。

### 架构兼容性
- Dockerfile 使用 `ARCH=$(uname -m)`（第39行）动态检测架构，避免硬编码 `aarch64` 或 `x86_64`，确保在不同 CI 节点上均可正确编译。

## 潜在风险
- FoundationDB 二进制（从 `foundationdb/foundationdb` 镜像中提取）基于 Rocky Linux 9.4 编译，运行时可能与 openEuler 24.03-LTS-SP3 的 glibc 存在版本兼容性差异。当前方案确保构建通过，但建议在运行时容器中验证 `fdbcli --version` 和 `libfdb_c.so` 链接正常。若出现运行时符号缺失，需改用源码编译或评估 `--nodeps` 提取方式。
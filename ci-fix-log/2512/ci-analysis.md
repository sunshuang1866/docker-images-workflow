# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM依赖不兼容
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), is needed by, foundationdb-clients, el9, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm …" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 硬编码下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`（EL9/RHEL 9 发行版 RPM），该 RPM 的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖在 openEuler 24.03 的 glibc/glibc-devel 包中无法被 rpm 依赖解析器识别满足，导致 `rpm -ivh` 安装失败。

### 与 PR 变更的关联
PR #2512 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行），其中第 22-24 行的 FoundationDB RPM 安装步骤使用了 EL9 构建的 RPM。该 RPM 与 openEuler 24.03 基础镜像的 glibc 符号版本方案不兼容，100% 由本次 PR 变更引入。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB 官方未提供 openEuler 原生 RPM，需改为从 FoundationDB 官方 Docker 镜像中提取客户端二进制文件（多阶段构建），或从源码自行编译 FoundationDB 客户端库并安装到镜像中，以规避跨发行版 RPM 依赖冲突。

### 方向 2（置信度: 中）
若 FoundationDB 官方提供通用 Linux 二进制 tar 包（非 RPM），可改用 tar 包直接解压安装。需查阅 FoundationDB 7.3.77 的发布页面确认是否有此类制品。

### 方向 3（置信度: 低）
尝试使用 `rpm -ivh --nodeps` 强制安装 RPM，但这可能导致运行时动态链接失败（libm GLIBC_2.17 符号缺失时 3FS 无法启动），仅作为临时验证手段，不推荐用于最终交付镜像。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否提供通用 Linux 二进制 tar.gz 包（非 RPM）可作为替代下载源
2. openEuler 24.03-LTS-SP3 的 glibc 是否实际包含 GLIBC_2.17 的 libm 符号（运行时可用但 RPM 元数据未声明），需要进入 live container 验证 `objdump -T /lib64/libm.so.6 | grep GLIBC_2.17`
3. 若 libm 符号实际存在，可考虑用 `rpmrebuild` 修改 RPM 的依赖声明，但更推荐方向 1/2
4. 构建日志中步骤 #11（git clone + cmake 编译 3FS）因步骤 #10 失败未执行，git 浅克隆与 commit hash checkout 的兼容性问题（参考模式18）是否存在尚无法验证，修复步骤 #10 后可能暴露新的构建错误

## 修复验证要求
若采用方向 1（多阶段构建从官方镜像提取二进制）：
- code-fixer 必须确认 FoundationDB 官方 Docker 镜像 `foundationdb/foundationdb:7.3.77` 在 Docker Hub 存在且包含所需的客户端二进制文件
- code-fixer 必须验证提取的二进制在 openEuler 容器中能正常运行（ldd 检查动态链接依赖均满足）

若采用方向 3（--nodeps 强制安装）：
- code-fixer 必须在 openEuler 24.03 容器中执行 `rpm -ivh --nodeps` 后运行 `ldd` 检查 FoundationDB 客户端二进制的所有动态链接依赖是否实际满足

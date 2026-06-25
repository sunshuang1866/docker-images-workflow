# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM依赖不兼容
- 新模式症状关键词: Failed dependencies, libm.so.6, GLIBC_2.17, rpm -ivh, el9, foundationdb, aarch64

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm \
  https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 官方发布的是面向 RHEL 9 (`el9`) 编译的 RPM 包，其 RPM 元数据中声明的 `libm.so.6(GLIBC_2.17)(64bit)` 依赖在 openEuler 的 glibc 包中未以相同 `Provides` 字符串提供（虽然底层 .so 实际包含该符号版本），导致 `rpm -ivh` 依赖检查失败。同时 Dockerfile 硬编码了 `aarch64` 架构的 RPM URL，当前 CI 构建环境实际运行在 x86_64 上（见 rustup 日志 `default host triple is x86_64-unknown-linux-gnu`），存在架构不匹配隐患。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，该 Dockerfile 第 22-24 行直接引入了 FoundationDB RPM 安装步骤，是该失败的**直接触发原因**。该步骤之前的 `yum install`、`rustup`、`fuse build`（步骤 7-9）均成功完成，失败发生在步骤 10。

## 修复方向

### 方向 1（置信度: 高）
**改用 `rpm -ivh --nodeps` 绕过 RPM 跨发行版依赖校验**，并用架构变量动态选择正确的 RPM URL：
1. 在 Dockerfile 开头使用条件判断当前构建架构（`uname -m`），将 `aarch64` / `x86_64` 映射为 FoundationDB 发布页面的架构标识（注意 FoundationDB 对 x86_64 可能使用 `amd64` 或 `x86_64`，需查看其 release 页面确认）
2. 将 `rpm -ivh` 改为 `rpm -ivh --nodeps` 跳过跨发行版 RPM 元数据依赖检查（实际 .so 文件由 openEuler 的 glibc 包提供，运行时无问题）
3. 验证 FoundationDB 7.3.77 的 x86_64 RPM 是否存在，若不存在该架构的 release，则需考虑备选方案

### 方向 2（置信度: 中）
**通过 FoundationDB 官方 Docker 镜像多阶段构建获取客户端二进制**（类似模式16）：
1. 使用 `FROM foundationdb/foundationdb:7.3.77 AS fdb-source` 作为构建源
2. `COPY --from=fdb-source /usr/bin/fdbcli /usr/lib/libfdb_c.so /usr/local/...` 复制所需文件
3. 参考模式16的历史案例（grafana-agent），绕过 RPM 安装的跨发行版兼容问题

## 需要进一步确认的点
1. FoundationDB 7.3.77 在 GitHub Releases 是否发布了 x86_64 (`amd64`) 架构的 RPM？当前 Dockerfile 只使用了 `aarch64` URL
2. FoundationDB 官方 Docker 镜像中是否包含构建 3FS 所需的客户端库文件（`libfdb_c.so` 及头文件）？如果 3FS 编译时需要 header 文件，多阶段构建方案需额外处理
3. 使用 `--nodeps` 安装后，FoundationDB 客户端在 openEuler 24.03 上运行时是否真正可用（glibc 版本兼容性需实际验证）

## 修复验证要求
1. 若采用方向 1：code-fixer 必须确认 FoundationDB 7.3.77 在 GitHub Releases 页面的 x86_64 RPM 文件名（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 或 `...amd64.rpm`），并在 x86_64 openEuler 24.03 容器中验证 `rpm -ivh --nodeps` 安装后 `fdbcli --version` 可正常执行
2. 若采用方向 2：code-fixer 必须拉取 `foundationdb/foundationdb:7.3.77` 镜像，确认其中包含 `libfdb_c.so` 和所有必需的客户端工具，并在 openEuler 24.03 容器中验证复制后的二进制能正常运行
3. 架构变量映射表必须参照 FoundationDB 实际 release 页面的文件命名验证，不允许猜测

# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码 RPM 不匹配
- 新模式症状关键词: Failed dependencies, libm.so.6(GLIBC_2.17)(64bit), aarch64.rpm, x86_64, foundationdb-clients

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`（FoundationDB RPM 安装步骤）
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构变体，当前 CI 构建在 x86_64 环境执行（由 fuse3 构建日志 `Host machine cpu: x86_64` 和 Rust 安装日志 `default host triple is x86_64-unknown-linux-gnu` 证实），aarch64 RPM 在 x86_64 系统上无法安装——`rpm -ivh` 报缺少 aarch64 版本的 `libm.so.6` 依赖。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（共 69 行，全新文件），该 Dockerfile 的第 22 行直接写死了 aarch64 专用的 FoundationDB RPM URL。此 URL 在 x86_64 CI runner 上必然失败。该问题是 PR 引入的新代码造成的，与已有代码无关。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 改为架构感知式：使用 Docker BuildKit 的 `TARGETARCH` ARG 或 shell `uname -m` 检测当前架构，根据架构选择对应的 RPM URL。FoundationDB 7.3.77 同时发布了 x86_64 和 aarch64 两个 RPM：
- `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

### 方向 2（置信度: 中）
如果 FoundationDB 的 EL9 RPM 在 openEuler 上存在 glibc 版本兼容性问题（即使架构正确），可以改为从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取 fdbcli 二进制文件，类似模式16 的多阶段构建方案。

## 需要进一步确认的点
1. FoundationDB RPM 在 openEuler 24.03 上是否存在除架构之外的其他依赖兼容性问题（如 glibc 版本、libstdc++ 版本等）。即使修正了架构选择，EL9 RPM 在基于 openEuler 的容器中安装时可能仍有隐含依赖冲突。
2. 该 Dockerfile 还有模式18 中已记录的 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true` 浅克隆问题（位于 Dockerfile 后续步骤），当前因构建在步骤 #10 提前失败而未触发，修复当前问题后该潜在问题仍需处理。

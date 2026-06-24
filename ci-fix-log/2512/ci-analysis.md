# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: `Failed dependencies`, `aarch64.rpm`, `foundationdb-clients`, `libm.so.6`, `rpm -ivh`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
ERROR: failed to solve: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`（FoundationDB RPM 安装步骤）
- 失败原因: 新增的 3FS Dockerfile 中 FoundationDB RPM 下载 URL 硬编码 `aarch64` 架构，但当前 CI 构建在 x86_64 机器上运行（日志中 fuse 构建输出 `Host machine cpu family: x86_64` 证实），导致 `rpm -ivh` 在 x86_64 系统安装 aarch64 包时依赖解析失败。此外 Dockerfile 中多处路径也硬编码了 aarch64（如 `aarch64-openEuler-linux-gnu`）。

### 与 PR 变更的关联
此失败是本次 PR 直接引入的。PR #2512 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，该 Dockerfile 全程假定目标架构为 aarch64：
1. FoundationDB RPM URL 硬编码 `aarch64`
2. Clang 库 symlink 路径使用 `aarch64-openEuler-linux-gnu`
3. `libclang_rt.builtins-aarch64.a` 硬编码 aarch64 后缀

PR 文档（README.md）声称支持 `amd64, arm64` 两种架构，但 Dockerfile 未做任何架构判断分支。

## 架构硬编码问题清单

除 FoundationDB 报错外，以下 Dockerfile 行也存在架构硬编码：

| 行号 | 硬编码内容 | 问题 |
|------|-----------|------|
| 22 | `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` | FoundationDB 下载 URL 锁定 aarch64 |
| 28-29 | `/usr/lib/clang/17/lib/aarch64-openEuler-linux-gnu/` | Clang 库路径仅含 aarch64 |
| 30 | `libclang_rt.builtins-aarch64.a` | 静态库目标名锁定 aarch64 |

## 修复方向

### 方向 1（置信度: 高）
FoundationDB RPM URL 需要支持两种架构。FoundationDB 7.3.77 发布了 `x86_64` 和 `aarch64` 两种 RPM。Dockerfile 需使用 BuildKit 的 `TARGETARCH` 变量或 Shell 条件判断来动态选择下载 URL。同时 Clang 库 symlink 路径也需要根据架构切换（x86_64 对应 `x86_64-openEuler-linux-gnu`，aarch64 对应 `aarch64-openEuler-linux-gnu`）。

### 方向 2（置信度: 低）
如果 3FS 确实无法在 x86_64 上构建（上游仅支持 aarch64），则需在 meta.yml 或 image-info.yml 中将架构限制为仅 aarch64，并确保 CI 只在 aarch64 runner 上构建此镜像。

## 需要进一步确认的点
1. FoundationDB 7.3.77 在 x86_64 上是否发布了对应 RPM（预期 URL: `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`），code-fixer 需验证该 URL 存在
2. 3FS 项目本身是否支持 x86_64 编译（CMakeLists.txt 中是否有架构特定代码）
3. openEuler 24.03-LTS-SP3 x86_64 基础镜像中 Clang 17 库的实际路径是否与 aarch64 版不同

## 修复验证要求
code-fixer 在提交修复前，必须：
1. 确认 FoundationDB 7.3.77 的 x86_64 RPM 可下载（`curl -sLI <x86_64_url>` 验证 200 响应）
2. 在 openEuler 24.03-LTS-SP3 x86_64 容器中验证 Clang 17 库路径（`find /usr/lib/clang -name "*.a" 2>/dev/null`）
3. 分别在 x86_64 和 aarch64 环境中完成完整构建验证（至少到 FoundationDB RPM 安装步骤通过）

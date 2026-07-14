# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, yum install failed

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

构建过程中还出现了多起恢复性网络错误（yum 自动重试后成功）：

| 时间点 | 失败的包 | Curl 错误码 | 是否最终成功 |
|--------|----------|-------------|-------------|
| #7 556.2 | gcc-12.3.1-110 | error (92) HTTP/2 INTERNAL_ERROR | 是 (#7 831.9 重试成功) |
| #7 836.2 | kernel-headers-6.6.0-159.4.3.154 | error (92) HTTP/2 INTERNAL_ERROR | 是 (#7 855.7 重试成功) |
| #7 1029.3 | perl-MIME-Base64-3.16-2 | error (56) SSL_ERROR_SYSCALL | 是 (#7 1030.5 重试成功) |
| #7 1310.2 | vim-common-9.0.2092-36 | error (92) HTTP/2 INTERNAL_ERROR | **否（最终失败）** |

### 根因定位
- 失败位置: `Dockerfile:4`（`RUN yum install -y ...` 步骤，具体为 yum 自动尝试下载 `vim-common` 时）
- 失败原因: CI aarch64 runner 在从 `repo.openeuler.org` 下载 RPM 包时遭遇间歇性网络故障（HTTP/2 流错误 `curl error 92` 和 SSL 读取错误 `curl error 56`），173 个待安装包中绝大多数通过 yum 自动重试机制成功下载，仅 `vim-common`（一个 `git`/`perl` 的间接依赖）在多次重试后耗尽所有镜像站仍未成功，导致整个 `yum install` 事务失败。

### 与 PR 变更的关联
**此失败与 PR 变更无关。**

PR 新增的 Dockerfile (`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`) 本身语法正确、包列表合理（`git gcc gcc-c++ make cmake which openssl-devel gflags-devel protobuf-devel protobuf-compiler abseil-cpp-devel leveldb-devel snappy-devel`）。失败的 `vim-common` 是 `git` 或其 Perl 依赖链引入的间接依赖，非 PR 显式声明的包。失败根因是构建时 `repo.openeuler.org` 仓库服务器与 CI runner 之间的网络连接不稳定，属于基础设施问题。

其余文件变更（`README.md` 新增一行表格、`image-info.yml` 新增一行表格、`meta.yml` 新增一个 tag 条目）均为元数据/文档级别的补充，不会触发任何构建步骤。

## 修复方向

### 方向 1（置信度: 高——非代码修复）
这是一个 **infra-error**，无需修改 PR 代码。`repo.openeuler.org` 仓库服务器在构建期间（2026-07-09 13:45 UTC 前后）存在 aarch64 架构的 HTTP/2 流稳定性问题。建议：

1. **重新触发 CI 构建**（retry）。网络波动通常是暂时的，重新构建大概率通过。
2. 若多次重试仍失败，可联系 openEuler 基础设施团队确认 `repo.openeuler.org` 的 aarch64 仓库服务状态。

### 方向 2（置信度: 低——缓解性优化，不推荐）
理论上可以在 Dockerfile 中为 `yum install` 添加 `--retries 10 --setopt=retries=10` 等参数增加网络容错，但对 HTTP/2 流协议层面的 `INTERNAL_ERROR` 效果有限；且同类 Dockerfile（如 `brpc/1.16.0/24.03-lts-sp3`）均无此类处理，不建议引入不一致的写法。

## 需要进一步确认的点
- `repo.openeuler.org` 在 2026-07-09 13:45 UTC 前后是否存在已知的服务降级或维护事件。
- 其他同时间段在该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建的其他 PR 是否也出现了类似的 yum 下载失败。

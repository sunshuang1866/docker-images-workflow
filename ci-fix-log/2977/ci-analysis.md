# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Yum仓库下载网络错误
- 新模式症状关键词: `Curl error (92)`, `Curl error (56)`, `INTERNAL_ERROR`, `SSL_ERROR_SYSCALL`, `repo.openeuler.org`, `yum install`, `No more mirrors to try`

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
------
Dockerfile:4
```

### 先行警告（非致命，但说明网络不稳定）
在整个 `yum install` 下载 173 个包的过程中，多次出现同类网络错误，但大部分通过重试恢复：
- `#7 556.2` gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92) — 重试后成功
- `#7 836.2` kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92) — 重试后成功
- `#7 1029.3` perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56) — 重试后成功
- `#7 1310.2` vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92) — **重试耗尽，最终失败**

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 yum 从 `repo.openeuler.org` 下载 173 个 RPM 包时，`repo.openeuler.org` 的 HTTP/2 连接持续出现 `INTERNAL_ERROR` 流错误（curl error 92），大多数包的下载通过镜像重试机制恢复，但 `vim-common` 包在所有镜像重试耗尽后仍无法下载，导致 `yum install` 退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个格式正确的 Dockerfile（定义 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的构建流程），以及更新了 README.md、image-info.yml 和 meta.yml。失败发生在 Docker 构建的第一步 `yum install` 阶段，这是从 openEuler 官方仓库下载系统依赖包的过程，失败的直接原因是 `repo.openeuler.org` 的 HTTP/2 层在向 aarch64 runner 传输 `vim-common` 包时反复中断。

## 修复方向

### 方向 1（置信度: 中）
**重试 CI 构建。** 该失败极大概率为 `repo.openeuler.org` 在构建时段（2026-07-09）对 aarch64 架构的 HTTP/2 服务出现间歇性问题（curl error 92/56）。173 个包中前 172 个均通过重试成功下载，仅 `vim-common` 失败，且所有错误均为网络层流中断而非 404/403，说明仓库内容本身无问题。重新触发 CI 大概率可通过。

### 方向 2（置信度: 低）
**如果多次重试仍失败**，可能 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库存在持续性的 HTTP/2 层不兼容问题。可尝试在 Dockerfile 的 yum 配置中强制降级为 HTTP/1.1（如 `echo "http2=false" >> /etc/yum.repos.d/*.repo` 在 RUN 命令开头执行），或临时换用其他镜像源。

## 需要进一步确认的点
1. 同一时段内其他 x86_64 runner 是否也出现类似网络错误？若 x86_64 构建正常而仅 aarch64 出问题，则可能是 `repo.openeuler.org` 对 aarch64 连接的服务端 HTTP/2 实现存在缺陷。
2. 同一时段其他使用 `openeuler:24.03-lts-sp4` 的 PR 是否也有相同失败？可据此判断是普适性网络问题还是 runner 节点特定问题。
3. `vim-common` 包的 RPM 文件大小约 7.8 MB，是此次下载中较大的单个文件之一，大文件传输更易触发 HTTP/2 流中断。后续若频繁出现类似错误，建议在 Dockerfile 中禁用 HTTP/2 或增加 yum 重试次数（`retries=10`）。

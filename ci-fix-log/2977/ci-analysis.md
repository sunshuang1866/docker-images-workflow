# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 镜像站的 openEuler 24.03-LTS-SP4 aarch64 仓库出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取错误（Curl error 56: SSL_ERROR_SYSCALL），导致 `vim-common` RPM 包下载失败。此前 `gcc`、`kernel-headers`、`perl-MIME-Base64` 也遭遇同类错误但重试后成功，`vim-common` 为最后一个待下载包（172/173 已完成），重试耗尽所有镜像后宣告失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 语法正确，`yum install` 安装的均为 openEuler 24.03-LTS-SP4 官方仓库中的标准包。失败根因是远端仓库服务器在构建时段的 HTTP/2 连接不稳定，属于 CI 基础设施/网络层面的瞬时故障。日志中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 等包也曾遭遇同类 Curl 错误但重试成功，说明仓库服务器在该时段存在间歇性问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。此失败为 `repo.openeuler.org` 镜像站的瞬时网络问题，与 PR 代码无关。等待镜像站恢复稳定后重试构建即可通过。

### 方向 2（置信度: 低）
若多次重试仍失败（说明镜像站该包确实存在问题），可考虑在 Dockerfile 的 `yum install` 前添加重试参数（如 `--retries 10 --retry-delay 10`），或跳过不需要的 `vim-common` 依赖（在 `yum install` 中添加 `--setopt=tsflags=nodocs` 或使用 `--skip-broken`，但更推荐的方式是排查为何 git 拉入 vim-common 并使用 `--exclude` 排除非必要依赖）。

## 需要进一步确认的点
1. `repo.openeuler.org` 镜像站在构建时段（2026-07-09 13:26-13:45 UTC）是否存在已知的故障/维护窗口。
2. `vim-common` 包在 openEuler 24.03-LTS-SP4 aarch64 仓库中是否确实可下载（手动 wget 验证该 URL）。
3. 是否存在大量同类 PR 在同一时段因相同原因失败（若广泛出现，说明镜像站大面积不稳定）。

# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf install, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: dnf 从 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR`）。其中 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 在所有镜像源均重试失败后，dnf 退出并返回错误码 1，导致整个 Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 这是一个纯粹的 CI 基础设施/网络问题。PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，该 Dockerfile 的 `dnf install` 命令语法正确、依赖包声明合理。失败发生在 `repo.openeuler.org` 的 aarch64 镜像仓库 HTTP/2 传输层面，与 PR 的 Dockerfile 内容、README 更新、`meta.yml` 或 `image-info.yml` 的任何修改均无因果关系。即使回退 PR 代码，同一 aarch64 runner 在同一时刻执行同一仓库的 `dnf install` 仍会触发相同的 HTTP/2 流错误。

## 修复方向

### 方向 1（置信度: 低）
等待 openEuler 镜像仓库 `repo.openeuler.org` 的 aarch64 HTTP/2 服务恢复后重试构建。该错误属于仓库服务端的 HTTP/2 协议层间歇性故障（HTTP/2 stream 非正常关闭），通常由服务端基础设施问题（如负载均衡器、反向代理、HTTP/2 连接管理组件）触发，与客户端代码无关。可尝试在非高峰时段重新触发 CI 构建。

### 方向 2（置信度: 低）
在 Dockerfile 的 `dnf install` 命令前添加 `dnf config-manager --setopt=max_parallel_downloads=1` 降低并发连接数，减少 HTTP/2 多路复用冲突的概率；或添加 `echo "retries=20" >> /etc/dnf/dnf.conf` 增加重试次数以容忍间歇性流错误。但这仅是对症缓解，不能从根本上解决仓库服务端的 HTTP/2 流问题。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库是否存在已知的 HTTP/2 服务不稳定或 CDN 节点故障。
- 同一 CI runner（`ecs-build-docker-aarch64-04-sp`）在同一时间段构建其他 openEuler 24.03-LTS-SP4 镜像时是否也遭遇相同的 HTTP/2 流错误，以确认问题是否为 aarch64 仓库的普遍性基础设施故障。
- `guile` 包重试失败而 `git-core` 最终成功，是否意味着不同 RPM 包被路由到不同的后端服务器/CDN 节点——部分节点正常、部分节点有 HTTP/2 故障。

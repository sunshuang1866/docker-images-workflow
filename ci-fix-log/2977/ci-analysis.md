# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum 镜像站 HTTP/2 传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Stream error, MIRROR, No more mirrors to try, yum install

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 命令）
- 失败原因: aarch64 构建节点 (`ecs-build-docker-aarch64-04-sp`) 在执行 `yum install` 时，从 `repo.openeuler.org` 下载 vim-common RPM 包过程中遭遇 HTTP/2 流传输错误（Curl error 92），yum 重试所有镜像后仍无法下载该包（173 个包中已成功下载 172 个，最后一个 vim-common 失败）。

值得注意的是，同一次 `yum install` 中还有另外 3 个包也遭遇了 HTTP/2 或 SSL 错误：
- `gcc-12.3.1-110.oe2403sp4.aarch64.rpm`: Curl error (92) — 重试后成功
- `kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm`: Curl error (92) — 重试后成功
- `perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm`: Curl error (56) — 重试后成功

这表明 `repo.openeuler.org` 在该时间段内对 aarch64 节点的 HTTP/2 连接存在间歇性不稳定。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Dockerfile 中 `yum install` 的包列表语法正确、包名均为 openEuler 24.03-LTS-SP4 仓库中的有效包（172/173 个已成功下载）。失败完全由 `repo.openeuler.org` 镜像站在 aarch64 节点的网络传输问题导致，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。该失败为临时性基础设施问题（`repo.openeuler.org` 对 aarch64 节点的 HTTP/2 连接不稳定）。重新触发 CI 构建（retry）即可，镜像站恢复后 yum install 应能正常完成。

### 方向 2（置信度: 低，仅在反复 retry 仍失败时考虑）
若多次 retry 后 vim-common 或类似包持续下载失败，可考虑在 Dockerfile 的 `yum install` 命令前添加 `yum makecache` 或在 `/etc/yum.repos.d/` 中添加其他可用镜像源来增加下载冗余。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否有已知的 HTTP/2 服务异常或网络波动
- 确认该 Dockerfile 在 x86_64 runner 上是否构建成功（日志仅展示了 aarch64 runner 的构建）
- 确认 retry 后构建是否通过

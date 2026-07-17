# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, aarch64, repo.openeuler.org, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 aarch64 RPM 仓库（`repo.openeuler.org`）在 HTTP/2 层反复返回服务端内部错误（`INTERNAL_ERROR (err 2)`），导致多个软件包下载失败。最终 `guile` 包耗尽所有镜像重试次数，dnf 安装过程退出码 1。此错误为服务端临时的 HTTP/2 协议层故障，与 Dockerfile 内容无关。

### 与 PR 变更的关联
PR 变更与此次失败无因果关系。该 PR 仅新增了一个标准的 vvenc Dockerfile（`24.03-lts-sp4` 版本），其中 `dnf install` 命令是仓库内标准写法。失败发生在 dnf 从 `repo.openeuler.org` 下载 RPM 包的 HTTP/2 传输层，属于 openEuler 镜像站服务端的临时/间歇性故障。日志中可见部分包（如 `git-core`）在重试后下载成功，另一部分（如 `gcc-c++`）重复出现流错误，而 `guile` 最终耗尽重试次数成为触发构建失败的最后一环——这进一步印证是服务端 HTTP/2 实现不稳定，而非 Dockerfile 配置问题。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败为 openEuler 镜像站 aarch64 SP4 仓库的临时 HTTP/2 服务端故障（`INTERNAL_ERROR`），是基础设施层面问题。直接重新运行 CI job 极大概率可以通过（或仅需一次重试）。

### 方向 2（置信度: 中）
若重试后仍然失败，可在 Dockerfile 的 `dnf install` 前添加 dnf 重试/超时配置（如 `echo 'retries=10' >> /etc/dnf/dnf.conf && echo 'timeout=120' >> /etc/dnf/dnf.conf`），提高对网络抖动的容忍度。但需注意这仅是对治方案，不解决服务端根因。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 aarch64 仓库在 CI 构建时间段（2026-07-09 14:00 UTC 左右）是否存在已知的服务端 HTTP/2 故障或维护窗口
- 同一时间窗口内其他依赖 SP4 仓库的镜像构建（如 `24.03-lts-sp4` 的其他 Dockerfile）是否也出现了类似错误——如果是，可确认是仓库服务端问题
- 此前 SP3 版本的 vvenc 镜像在同一 aarch64 runner 上是否构建稳定（用于对比排除 runner 网络环境问题）

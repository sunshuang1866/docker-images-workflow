# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF 镜像站 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: DNF 从 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）遭遇 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`，`INTERNAL_ERROR (err 2)`）。`gcc-c++` 在两次重试均失败后，DNF 耗尽所有镜像重试，报 "No more mirrors to try"，整个安装步骤退出码为 1。根因是仓库服务器的 HTTP/2 实现在处理大文件下载时存在协议层问题（stream 被异常关闭），属于 CI 基础设施 / 上游镜像站网络问题。

### 与 PR 变更的关联
**与 PR 变更无关**。PR #2980 的变更仅为新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（以及配套的 README.md、image-info.yml、meta.yml 条目），Dockerfile 内容本身无语法或逻辑错误。失败发生在 `dnf install` 从远程仓库下载 RPM 包的阶段，这是上游 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 协议层问题，并非 PR 代码引入的错误。其他镜像（如 cmake-data、git-core）也在同一构建中遭遇了相同的 HTTP/2 流错误，进一步表明是仓库端的问题。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库恢复后重试构建**。此为上游 openEuler 24.03-LTS-SP4 RPM 仓库的 HTTP/2 服务器端临时故障，无需修改 Dockerfile。在仓库服务恢复后，重新触发 CI 构建即可通过。属于典型的 infra-error，Code Fixer 无需处理。

### 方向 2（置信度: 中）
**降级 libcurl/HTTP 协议或更换镜像源**。如果该仓库持续不稳定，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 或 `echo "http2=false" >> /etc/dnf/dnf.conf` 将 DNF 的 libcurl HTTP 协议从 HTTP/2 降级为 HTTP/1.1，或替换为其他可用的 openEuler 24.03-LTS-SP4 镜像源。但此方向属于临时 workaround，非根本修复，且需确认替代镜像源在 CI 环境中可达。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 x86_64 RPM 仓库）在 CI 构建环境中的当前可达性及 HTTP/2 服务状态。
- 确认该仓库是否有替代镜像源可用，以及替代源在 CI 网络环境中是否可达。
- 若该问题持续出现，需确认是仓库服务器端问题还是 CI 网络代理/防火墙干扰了 HTTP/2 长连接。

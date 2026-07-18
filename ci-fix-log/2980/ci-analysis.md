# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库的 HTTP/2 服务端连接不稳定，258 个包中的 3 个（cmake-data、git-core、gcc-c++）在下载过程中遭遇 HTTP/2 协议层 INTERNAL_ERROR。cmake-data 和 git-core 重试后下载成功，gcc-c++（13 MB）重试两次仍全部失败，DNF 耗尽所有镜像源后报错退出。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 仅新增了一个正确的 Dockerfile（添加 openEuler 24.03-LTS-SP4 对 GrADS 2.2.3 的支持）及配套元数据文件。Dockerfile 中的 `dnf install` 命令语法正确、包名无误，失败完全由 openEuler 仓库服务器端的 HTTP/2 协议故障导致。该 Dockerfile 在仓库恢复正常后有很大概率直接构建成功。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试**。这是 openEuler 官方 RPM 仓库 HTTP/2 服务的临时性故障（Curl error 92: HTTP/2 stream INTERNAL_ERROR），与 PR 代码无关。等待仓库服务恢复后，重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
**在 Dockerfile 中禁用 HTTP/2 回退到 HTTP/1.1**。在 `dnf install` 前设置环境变量 `RUSTLS_HTTP2=0` 或配置 dnf 的 `http2=false`，强行将 curl/libcurl 降级为 HTTP/1.1 协议下载 RPM 包。不推荐此方向，因为这是绕过而非修复问题，且 HTTP/1.1 对大量小文件的并发下载效率低于 HTTP/2。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在 CI 构建时段是否存在已知的 HTTP/2 服务端异常或维护窗口。
2. 验证同样使用 `openeuler/openeuler:24.03-lts-sp4` 基础镜像的其他 PR 在同时段是否也出现相同错误（判断是否为仓库侧全局性问题）。
3. 确认 CI 构建节点的网络链路是否存在 HTTP/2 长连接被中间设备（代理、防火墙）异常断开的情况。

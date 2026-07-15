# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, [MIRROR], No more mirrors to try, gcc-c++

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在传输 `gcc-c++` 等 RPM 包时反复出现 HTTP/2 流帧错误（Curl error 92: INTERNAL_ERROR），导致 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 下载失败，所有镜像均已尝试后仍无法成功，dnf 安装步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码无关**。PR #2980 新增的 Dockerfile 内容在语法和语义上均正确——`dnf install` 命令中列出的所有包（gcc、gcc-c++、cmake 等）都是 openEuler 24.03-LTS-SP4 仓库中真实存在的包（日志中 dnf 已成功解析了 258 个包的依赖关系），且部分包（如 binutils、gettext、gcc 本体等）已成功下载。失败的根本原因是 CI 构建环境与 openEuler 软件包仓库之间的网络链路存在 HTTP/2 协议层面的抖动，Dockerfile 代码本身不需要修改。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该失败属于 CI 基础设施层面的瞬时网络问题（openEuler 24.03-LTS-SP4 仓库 HTTP/2 流不稳定），非代码缺陷。直接重新触发 CI 构建流水线，有较大概率成功通过（日志中 `cmake-data` 和 `git-core` 在首次 MIRROR 错误后均通过重试下载成功，说明网络问题是间歇性的）。

### 方向 2（置信度: 中）
若多次重试仍持续失败，可能存在特定镜像站点持续不可用的问题。此时可在 Dockerfile 的 `dnf install` 前添加 `RUN echo 'http2=false' >> /etc/dnf/dnf.conf` 或类似配置，强制 dnf/libcurl 回退到 HTTP/1.1 协议，规避 HTTP/2 帧层不稳定问题。但此方案为 workaround 而非根本修复，不建议作为首选。

## 需要进一步确认的点
1. 该 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）是否为 CI 专用的内部镜像代理？若为内部代理，需排查代理服务器的 HTTP/2 实现是否存在已知缺陷。
2. 是否仅 `gcc-c++` 包（~13MB）因体积较大更容易触发 HTTP/2 流中断？日志中同样较大的 `gcc`（~34MB，下载耗时 7 分 28 秒）和 `cmake`（~16MB）反而下载成功，说明问题并非完全由包大小决定。
3. 重试构建时建议对比不同时间段（如非高峰时段）的网络状况，以排除仓库服务端负载过高导致的流中断。

## 修复验证要求
（无需填写——本失败为 infra-error，不涉及代码修改，无正则 patch 相关验证需求。）

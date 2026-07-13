# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake autoconf automake libtool pkgconf-devel       readline-devel ncurses-devel       libX11-devel libXaw-devel libXrender-devel libXext-devel libXt-devel       zlib-devel libpng-devel libjpeg-turbo-devel       curl-devel libxml2-devel       cairo-devel pixman-devel fontconfig-devel freetype-devel       gd-devel jasper-devel       libgeotiff-devel libtiff-devel proj-devel       git &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 构建节点在执行 `dnf install` 时，与 openEuler 24.03-LTS-SP4 RPM 仓库之间的 HTTP/2 连接反复出现流层协议错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），涉及 `cmake-data`、`git-core`、`gcc-c++` 三个包均遭此错误。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++` 在所有镜像均已尝试后仍失败，导致 `dnf install` 整体退出码为 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 语法正确、`dnf install` 包名列表完整。失败是 CI 构建节点与 openEuler RPM 镜像站之间的 HTTP/2 传输层间歇性故障，属于 CI 基础设施层面的网络问题。Dockerfile 本身无任何错误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该失败为 CI 基础设施与上游 RPM 镜像站之间的 HTTP/2 协议层间歇性网络故障，与代码变更无关。Code Fixer 无需修改任何文件，重新触发 CI 流水线大概率可以通过。

### 方向 2（置信度: 低）
若多次重试均在同一下载环节失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 或调整 DNF 配置中的 `retries`/`timeout` 参数，增加网络容错能力。但从当前日志看，DNF 已经进行了自动重试（多个 MIRROR 切换），只是最终 gcc-c++ 耗尽了所有镜像。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 RPM 镜像站（`repo.****.org`）在 CI 构建时间段是否存在服务端 HTTP/2 处理异常或负载过高的问题。
- 确认 CI 构建节点（`ecs-build-docker-x86-03-sp`）的网络出口是否存在 HTTP/2 代理或防火墙干扰。

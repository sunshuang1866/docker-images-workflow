# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake autoconf automake libtool pkgconf-devel       readline-devel ncurses-devel       libX11-devel libXaw-devel libXrender-devel libXext-devel libXt-devel       zlib-devel libpng-devel libjpeg-turbo-devel       curl-devel libxml2-devel       cairo-devel pixman-devel fontconfig-devel freetype-devel       gd-devel jasper-devel       libgeotiff-devel libtiff-devel proj-devel       git &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）下载 RPM 包时，HTTP/2 连接反复出现流错误（Curl error 92: INTERNAL_ERROR），导致 `gcc-c++` 包重试耗尽所有镜像后下载失败，进而整个 `dnf install` 命令失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）语法正确，`dnf install` 命令中声明的所有包名均为 openEuler 24.03-LTS-SP4 仓库中真实存在的包（从日志依赖解析阶段可确认，258 个包均被 dnf 成功识别并进入下载阶段）。失败发生在下载阶段，且多个不同包（`cmake-data`、`git-core`、`gcc-c++`）均遭遇了同样的 HTTP/2 流错误，这是 openEuler 软件仓库镜像的网络层问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码。** 这是 CI 基础设施层面的网络问题，openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）的 HTTP/2 服务在构建时段不稳定。建议：
- 等待镜像仓库恢复后触发 CI 重试（re-run failed job）。
- 若该问题持续出现，可考虑联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 服务端配置。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库在构建时段（2026-07-13 07:04 UTC）是否存在已知的服务不稳定问题。
- 该仓库镜像的 HTTP/2 配置是否有变更，导致批量下载时频繁触发 `INTERNAL_ERROR`。
- 如果 CI 重试后仍然失败（且是同一类 HTTP/2 错误），需要确认是仓库端问题还是 CI 构建节点到仓库之间网络链路的持续性问题。

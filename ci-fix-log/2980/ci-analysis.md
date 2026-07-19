# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时，连续在两个不同镜像上遭遇 HTTP/2 协议层流错误（Curl error 92: Stream error in the HTTP/2 framing layer，`INTERNAL_ERROR (err 2)`），所有可用镜像均已尝试后该包仍未下载成功，导致 `dnf install` 整个事务失败。日志中另外两个包（`cmake-data`、`git-core`）也出现相同 HTTP/2 流错误，但通过其他镜像重试后成功下载，说明这是镜像站协议层的不稳定问题而非代码错误。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了一个 GrADS 2.2.3 的 Dockerfile 及对应的 README、meta.yml、image-info.yml 条目。失败发生在 Docker 构建的 `dnf install` 阶段——从 openEuler 24.03-LTS-SP4 官方仓库下载系统编译工具链包（gcc-c++ 等）时，因镜像站 HTTP/2 协议故障导致下载失败。`dnf install` 中的包名均正确，PR 引入的 Dockerfile 语法和逻辑无误。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该失败属于镜像站基础设施的临时间歇性故障（HTTP/2 framing layer INTERNAL_ERROR）。3 个受影响的包中有 2 个（cmake-data、git-core）通过镜像切换重试成功，仅 gcc-c++ 在所有可用镜像上都遇到流错误。应在数小时/一天后重新触发 CI 构建，镜像站 HTTP/2 问题大概率已自愈。无需修改任何代码。

### 方向 2（置信度: 低）
若多次重试后 gcc-c++ 包仍持续在多个镜像上出现 HTTP/2 流错误，需排查是否是该特定 RPM 文件在镜像间同步时损坏。此时需要联系 openEuler 24.03-LTS-SP4 仓库维护方确认 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在源站的完整性和镜像同步状态。

## 需要进一步确认的点
1. 当前镜像站 HTTP/2 协议层是否已恢复稳定——直接重新触发 CI 构建即可验证。
2. 若重试后同一 gcc-c++ 包仍失败，需确认该 RPM 文件在 openEuler 24.03-LTS-SP4 官方源站上是否完整存在且未被损坏。
3. 是否存在 SPDX/Copyright 声明缺失等其他预检问题——当前日志中构建在 `dnf install` 阶段即失败，后续的 license 检查等步骤未被执行，需在构建通过后方能确认。

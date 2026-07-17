# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, gcc-c++, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.***.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.***.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.***.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.***.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake autoconf automake libtool pkgconf-devel       readline-devel ncurses-devel       libX11-devel libXaw-devel libXrender-devel libXext-devel libXt-devel       zlib-devel libpng-devel libjpeg-turbo-devel       curl-devel libxml2-devel       cairo-devel pixman-devel fontconfig-devel freetype-devel       gd-devel jasper-devel       libgeotiff-devel libtiff-devel proj-devel       git &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 openEuler 24.03-LTS-SP4 软件包仓库下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（13 MB）时，仓库镜像服务器多次返回 HTTP/2 帧层流错误（`Curl error (92)`, `INTERNAL_ERROR`），重试耗尽所有可用镜像后下载失败，导致整个 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Grads 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile（以及相应的 README.md、image-info.yml、meta.yml 更新）。Dockerfile 中的 `dnf install` 命令语法和包名均正确无误（共有 258 个包被列入事务清单，其中大部分已成功下载）。失败纯粹是因为 openEuler 24.03-LTS-SP4 的 `repo.***.org` 镜像站在该时间点存在 HTTP/2 服务端不稳定问题——`cmake-data` 和 `git-core` 也遇到了相同的 `Curl error (92)`，但它们在重试后成功下载；而 `gcc-c++` 因体积较大（13 MB），在 HTTP/2 流中断后重试了所有镜像均未成功。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该错误为 openEuler 24.03-LTS-SP4 软件包仓库镜像的瞬时网络故障（HTTP/2 服务端不稳定），与 PR 代码完全无关。在仓库镜像恢复稳定后，重新触发 CI 构建即可通过。若多次重试仍持续失败，可考虑更换 `dnf` 镜像源配置或检查 CI runner 所在网络与 `repo.***.org` 之间的 HTTP/2 兼容性问题。

## 需要进一步确认的点
- 该 `repo.***.org` 镜像站的 HTTP/2 服务稳定性是否在特定时段存在已知问题。
- 是否所有 openEuler 24.03-lts-sp4 的 Docker 构建（不止本次 grads PR）在同一时间段都遇到了该镜像站的相同错误。若为批次性问题，可能需要在 CI 环境层面解决（如降级为 HTTP/1.1 或更换镜像源），而非针对单个 PR 修复。

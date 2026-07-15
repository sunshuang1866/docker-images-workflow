# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, not closed cleanly, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 时反复返回 HTTP/2 流错误（Curl error 92），dnf 重试所有可用镜像均失败，导致 258 个包的安装事务中断。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 语法正确，`dnf install` 命令的参数和包名均无问题。失败纯粹是因为 CI 构建环境访问 openEuler 仓库镜像时遇到 HTTP/2 传输层错误——`cmake-data`、`git-core`、`gcc-c++` 三个包先后触发 `Curl error (92)`，前两个经重试成功下载，`gcc-c++` 在两次重试后仍未成功，耗尽所有可用镜像。

## 修复方向

### 方向 1（置信度: 高）
无需修复代码。此失败为偶发的 CI 基础设施问题（仓库镜像 HTTP/2 连接不稳定），与 PR 代码变更无关。触发 CI 重试即可——在 PR 评论中回复触发指令重新运行构建，大概率可自然通过。

### 方向 2（置信度: 低）
如果同一 PR 多次重试仍反复出现相同错误，可在 Dockerfile 的 `dnf install` 命令中添加 `--retries 5` 或 `--setopt=retries=5` 参数增加下载重试次数，以提高对临时性网络波动的容忍度。但根据当前日志，已有重试机制（`cmake-data` 和 `git-core` 均在一次镜像错误后重试成功），`gcc-c++` 两次重试均失败说明问题在于上游仓库持续不可用，而非重试次数不足。

## 需要进一步确认的点
- 无需进一步确认。日志清晰地表明失败根因是仓库镜像 HTTP/2 流错误，与 PR 内容无关。
- 若需验证，可在该 PR 上重新触发 CI 构建；若通过则确认本次失败为临时性网络异常。

# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf, repo

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 协议层存在稳定性问题，导致大文件（gcc-c++ 13MB）下载时 HTTP/2 stream 异常关闭（`INTERNAL_ERROR`），dnf 在耗尽所有镜像重试后放弃下载。其他受影响但成功恢复的包包括 cmake-data（2.1MB）和 git-core（11MB），gcc（34MB）也意外成功。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 语法和包名均正确，`dnf install` 命令本身没有问题。失败纯粹由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端协议错误引起，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是临时性的基础设施问题（仓库镜像 HTTP/2 stream 异常），通常重试即可通过。日志中 cmake-data 和 git-core 在首次 HTTP/2 错误后通过镜像重试成功下载，gcc-c++ 恰好两次都命中故障镜像。该问题与 PR 代码无关，不需要修改任何文件。

## 需要进一步确认的点
- 若反复重试均失败，需确认 openEuler 24.03-LTS-SP4 仓库镜像是否长期存在 HTTP/2 协议不兼容问题，此时可考虑在 Dockerfile 中为 `dnf` 添加 `--setopt=retries=10` 增加重试次数，或配置回退到 HTTP/1.1（`http2=false`）。

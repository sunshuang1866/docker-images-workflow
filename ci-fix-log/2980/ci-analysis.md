# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success

#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库服务器返回 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`，服务端报 `INTERNAL_ERROR (err 2)`）。dnf 内置的重试机制使部分包（cmake-data、git-core）最终下载成功，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（13MB）经历两次 HTTP/2 流中断后耗尽所有镜像重试机会，下载失败。

### 与 PR 变更的关联
本次 PR 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，Dockerfile 中 `dnf install` 步骤所列的依赖包列表语法正确、包名合法（从日志中"258 Packages"和"Installed size: 1.3 G"可见依赖已成功解析）。构建失败**与 PR 代码变更无关**，是 openEuler 24.03-LTS-SP4 软件仓库镜像站的 HTTP/2 服务端问题导致的基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题（openEuler 24.03-LTS-SP4 仓库服务器的 HTTP/2 协议栈间歇性错误），**无需修改 Dockerfile 代码**。操作建议：
- 等待仓库镜像站恢复后**重试 CI**（re-run the failed job）
- 如果持续出现此问题，联系 openEuler 基础设施团队排查仓库端的 HTTP/2 proxy/CDN 配置

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库当前是否存在 HTTP/2 服务故障（可检查同一时间段其他 openEuler 24.03-LTS-SP4 镜像的构建是否也出现类似 Curl error 92）
- 如果该仓库的 HTTP/2 问题频繁发生，可考虑在 `dnf install` 命令前添加 `echo 'http2=false' >> /etc/dnf/dnf.conf` 临时禁用 HTTP/2 作为规避手段（但这属于基础设施层面的 workaround，更建议从源头修复仓库服务）

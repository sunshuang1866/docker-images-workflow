# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建节点（x86_64 runner）与 openEuler 24.03-LTS-SP4 软件包仓库之间的 HTTP/2 连接出现流帧错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），导致 `cmake-data`、`git-core`、`gcc-c++` 三个 RPM 包下载中断。前两者通过重试成功恢复下载，但 `gcc-c++` 在两次 HTTP/2 流错误重试后耗尽所有镜像源，最终 `dnf install` 因无法下载该包而失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增了一个标准格式的 Dockerfile，`dnf install` 中的依赖包列表均属于 openEuler 24.03-LTS-SP4 仓库的常规可用包（cmake 3.31.12、gcc 12.3.1、git 2.54.0 等），不存在拼写错误或版本不存在的问题。失败完全由 CI 构建环境与上游软件包仓库镜像之间的 HTTP/2 连接问题导致，属于临时性基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重新运行。** 此失败为临时性网络/基础设施问题（HTTP/2 流中断），非代码缺陷。直接重新触发 CI Job 即可。如果同一 PR 重复出现此问题，则需要检查 CI runner 节点到 `repo.****.org` 的网络链路质量，或联系仓库运维排查 HTTP/2 服务端配置。

### 方向 2（置信度: 低）
如反复出现，可在 `dnf install` 命令前添加 `echo 'http2=0' >> /etc/dnf/dnf.conf` 将 dnf 的 libcurl 降级为 HTTP/1.1，绕过 HTTP/2 流帧问题。但这属于规避而非根因修复，应优先由仓库运维侧解决 HTTP/2 服务端问题。

## 需要进一步确认的点
1. 同一时间段是否有其他 PR 的 x86_64 构建也因相同報错失败？若多个 PR 同时失败，可确认是仓库侧 HTTP/2 服务的共性问题。
2. `repo.****.org` 的 openEuler 24.03-LTS-SP4 仓库 HTTP/2 服务是否存在已知故障或处于维护窗口期。
3. gcc-c++ 包（12.3.1-110.oe2403sp4，13 MB）相对较大，是否更容易触发 HTTP/2 流中断。日志中 cmake-data（2.1 MB）和 git-core（11 MB）虽然也遇到了流错误，但都在一次重试后成功下载。

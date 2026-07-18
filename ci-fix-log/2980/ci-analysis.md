# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, INTERNAL_ERROR

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器在 HTTP/2 传输层反复出现 stream 中断错误（`INTERNAL_ERROR`），导致 `gcc-c++` 等 RPM 包下载失败，`dnf` 在所有 mirror 均尝试失败后报错退出。`cmake-data` 和 `git-core` 虽然有同样的 HTTP/2 stream 错误，但最终重试成功完成下载；`gcc-c++` 两次重试均失败，触发了 `No more mirrors to try` 致命错误。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个标准结构的 Dockerfile（安装编译依赖 → clone 源码 → 编译安装），`dnf install` 命令中列出的包名均正确无误。失败源于 openEuler 24.03-LTS-SP4 的官方仓库镜像在 CI 构建时段出现 HTTP/2 传输不稳定，属于 CI 基础设施/网络问题。由于这是该 Dockerfile 的首次构建，无缓存可利用，大量包（258 个）完全依赖远程仓库下载，放大了网络不稳定带来的失败风险。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 该故障是仓库镜像服务器在 HTTP/2 传输层产生的瞬时网络错误（`Stream error in the HTTP/2 framing layer`），与 Dockerfile 内容无关。待 openEuler 镜像仓库网络恢复正常后，重新触发 CI 构建即有望通过。

### 方向 2（置信度: 低）
**如需增强构建稳定性**，可在 `dnf install` 命令前添加 `dnf makecache` 预热缓存，或在 `dnf install` 中追加 `--retries 5` 参数以提高网络波动时的容错能力。但此优化非必须，镜像仓库的 HTTP/2 stream 错误属于临时性基础设施问题。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的仓库镜像（`repo.****.org`）在 CI 构建时段是否经历了服务不稳定或网络抖动。
- 若有条件，在同一 CI runner 上对 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 做一次手动 `curl -I` 测试，排除该特定包在仓库中被损坏的可能。

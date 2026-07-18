# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y       gcc gcc-c++ make cmake autoconf automake libtool pkgconf-devel ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 传输层出现多次流中断错误（Curl error 92），导致 `cmake-data`、`git-core`、`gcc-c++` 三个 RPM 包的下载均受波及。`gcc-c++` 在所有可用镜像均尝试失败后，dnf 放弃并报错退出。

### 与 PR 变更的关联

**与 PR 代码无关。** 该 PR 新增的 Dockerfile 语法正确、依赖声明完整，`dnf install` 命令本身没有问题。失败是 openEuler 仓库镜像服务端的 HTTP/2 协议栈出现偶发故障，属于 CI 基础设施层面的网络问题。

影响范围：仅影响 `dnf install` 步骤中需要从仓库下载 RPM 包的构建阶段。其他已缓存的包（如部分依赖）下载成功，约 40/258 个包完成了下载，说明仓库并非完全不可达，而是 HTTP/2 连接在传输过程中间歇性中断。

## 修复方向

### 方向 1（置信度: 高）
**触发重试。** 这是 openEuler 仓库镜像的临时性网络故障，与 PR 代码无关。等待仓库服务恢复后重新触发 CI 构建即可，大概率会通过。无需修改 Dockerfile 或任何代码文件。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像在该时段是否存在已知的服务中断或降级事件。
- 如果多次重试后仍持续失败，需排查是否为 CI 构建节点与仓库之间的网络路由问题，或仓库是否已更换域名/URL。

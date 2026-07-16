# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success

#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像服务器在处理 HTTP/2 连接时发生内部流错误（`INTERNAL_ERROR (err 2)`），导致 dnf 下载 `gcc-c++` 等 RPM 包时连接被异常关闭。虽然部分包（cmake-data、git-core）在自动重试后下载成功，但 `gcc-c++` 两次重试均失败并耗尽所有镜像源，最终 dnf 安装失败。

### 与 PR 变更的关联
与 PR 变更**无直接关联**。PR 新增的 Dockerfile 本身语法正确、`dnf install` 命令格式无问题。失败原因是 CI 构建环境的网络/仓库镜像基础设施问题——openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务端在当前时段不稳定，导致大型 RPM 包（gcc-c++ 13MB）下载反复失败。属于偶发性网络故障，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该错误为 openEuler 24.03-LTS-SP4 仓库镜像服务端的 HTTP/2 瞬态故障，具有自愈特性。等待仓库服务恢复后重新触发 CI 构建即可通过。cmake-data 和 git-core 在自动重试后已成功下载，说明镜像站并非完全不可用，只是个别大文件在特定时段下载不稳定。

### 方向 2（置信度: 中）
**在 Dockerfile 中为 dnf 添加重试机制**。若该仓库镜像的不稳定问题持续出现，可在 `dnf install` 命令中添加重试参数（如 `dnf install --retries 5 -y ...`），或事先配置 dnf 禁用 HTTP/2、强制使用 HTTP/1.1 以避免 HTTP/2 流错误。但需注意此类修改属于对基础设施问题的 workaround，应在确认问题持续复现后才考虑。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端不稳定是否为已知问题，是否需要上报仓库运维团队
- 同一时段其他依赖于 openEuler 24.03-LTS-SP4 仓库的 CI job 是否也遇到了相同的 HTTP/2 流错误
- 如果该问题在多次重试后仍然出现，需要排查是否为 CI 构建节点的网络代理/防火墙与 HTTP/2 协议的兼容性问题

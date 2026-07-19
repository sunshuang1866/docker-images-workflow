# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo mirror

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`dnf install` 步骤，Docker 构建阶段 `[2/3]`）
- 失败原因: CI 构建环境中 dnf 从 openEuler 24.03-LTS-SP4 软件仓库镜像下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 协议层流错误（`Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`）。cmake-data 和 git-core 重试后成功下载，但 gcc-c++（13MB）经过两次镜像重试均失败，dnf 耗尽所有可用镜像后报错退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（GrADS 构建镜像）及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 包列表语法正确，包名在 openEuler 24.03-LTS-SP4 仓库中真实存在（从日志可见依赖解析完成后列出了 258 个待安装包）。失败根因是 openEuler 软件仓库镜像端的 HTTP/2 协议实现存在间歇性缺陷，与 PR 的 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试（re-run failed jobs）。** 这是典型的网络/基础设施瞬时故障。从日志可见 cmake-data 和 git-core 在重试后成功下载，仅 gcc-c++ 因连续两次 HTTP/2 流错误而耗尽重试次数。openEuler 仓库镜像的 HTTP/2 问题通常是间歇性的，重新触发构建大概率会成功。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
**在 dnf 配置中禁用 HTTP/2 或切换镜像源。** 如果多次重试仍然失败，可在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或更换仓库镜像地址。但这属于规避方案而非根因修复，且可能影响其他已有 Dockerfile 的一致性，建议仅在上游仓库镜像持续不可用时采用。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）的 HTTP/2 服务是否在当前时间段内存在已知的稳定性问题。
- 如果重试后仍然失败，需要确认是否需要将下载源切换到其他可用的 openEuler 软件源镜像站。

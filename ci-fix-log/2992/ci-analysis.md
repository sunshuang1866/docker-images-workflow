# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 yum 仓库 (`repo.****.org`) 在通过 HTTP/2 提供 RPM 包下载时，持续出现协议层 stream 错误（Curl error 92, INTERNAL_ERROR），多个软件包（gcc-gfortran、glibc-devel、gcc、guile）受影响。`gcc` 包（34 MB）在所有镜像重试耗尽后仍未下载成功，导致 `dnf install` 整体失败，进而触发 builder 阶段构建失败，并级联取消 stage-1 阶段。

### 与 PR 变更的关联
**无关。** PR 变更仅为新增 `24.03-lts-sp4` 的 Dockerfile 及相应的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 中的 `dnf install` 命令列出的软件包（git、gcc、gcc-c++、gcc-gfortran、make、openblas-devel、lapack-devel）均为 openEuler 24.03-LTS-SP4 仓库中的标准包，命令语法正确。错误源自 yum 仓库服务器端的 HTTP/2 协议层问题，与 PR 代码变更无任何因果关联。此外，日志中并行的 stage-1 阶段（#7）也遭遇完全相同的 Curl error (92)，进一步证实这是仓库侧的系统性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此为 CI 基础设施的仓库镜像 HTTP/2 服务端问题。建议操作：
- 重新触发 CI 构建，等待镜像仓库恢复稳定后重试
- 若持续失败，联系运维排查 `repo.****.org` 的 HTTP/2 代理/负载均衡器配置（nginx/haproxy 等），检查是否存在 HTTP/2 stream 超时或缓冲区配置不当导致大文件传输时流中断

## 需要进一步确认的点
- 该仓库镜像 (`repo.****.org`) 在 CI 失败时间段的可用性状态，是否其他依赖该仓库的 SP4 构建任务也同期失败
- 仓库服务端的 HTTP/2 配置（如 nginx 的 `http2_max_field_size`、`proxy_read_timeout`、`http2_recv_timeout` 等），排查大文件下载时 stream 中断的根因

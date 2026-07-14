# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: openEuler 24.03-LTS-SP4 的软件包仓库镜像（`repo.****.org`）在 HTTP/2 协议层出现流错误（`INTERNAL_ERROR (err 2)`），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。`dnf` 尝试了所有可用镜像后均失败，最终 `gcc` 包因"所有镜像均已尝试但无成功"而致命失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 语法正确，`dnf install` 命令本身无错误。失败是由 openEuler 24.03-LTS-SP4 仓库镜像服务端的 HTTP/2 协议问题引起的，属于 CI 基础设施层面的故障。日志中 stage-1 构建（#7）也出现了相同的 MIRROR 错误（`glibc-devel`、`gcc-gfortran`），进一步佐证这是镜像仓库侧的普遍性问题，而非特定 Dockerfile 或特定软件包的个别问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性基础设施故障。Code Fixer 无需处理，等待仓库镜像恢复后重新触发 CI 即可。若该问题持续出现，可考虑在 Dockerfile 的 `dnf install` 前增加 `dnf makecache` 或调整 `/etc/dnf/dnf.conf` 中的重试参数（如 `max_retries`、`retries`）以增强容错能力。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）当前状态是否正常。可尝试手动 `curl -I` 访问日志中的 RPM 包 URL 验证 HTTP/2 连接是否恢复。
2. 检查是否存在可替换的备用镜像源（如 `repo.huaweicloud.com` 等），若主镜像长期不稳定可考虑切换。
3. 确认 stage-1（运行时阶段）构建（#7）的类似 MIRROR 错误是否也导致了失败——日志显示 #7 被 `CANCELED`，暗示 stage-1 阶段的包下载也可能因同样问题受阻，只是在被取消前未达到致命失败点。

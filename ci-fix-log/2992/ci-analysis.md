# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 包仓库（`repo.****.org`）在 CI 构建期间出现 HTTP/2 协议层错误，curl 在下载多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）时收到 `INTERNAL_ERROR` 流关闭，所有镜像重试均失败，`dnf install` 无法完成。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅为新增 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。失败原因是 openEuler 24.03-LTS-SP4 官方包仓库的网络/服务端 HTTP/2 流错误，属于 CI 基础设施问题。同一构建中两个独立的 dnf 阶段（builder 的 #8 和 final stage 的 #7）均受到了同一仓库的 HTTP/2 流错误影响，进一步证明这是仓库端的服务问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是 openEuler 24.03-LTS-SP4 包仓库的临时性网络/服务端故障（HTTP/2 INTERNAL_ERROR），PR 代码本身无问题。等待仓库恢复后重新运行 CI 即可。

### 方向 2（置信度: 低）
如果该仓库持续出现 HTTP/2 问题，可考虑在 Dockerfile 的 `dnf install` 前强制降级为 HTTP/1.1（如通过 `echo "http2=false" >> /etc/dnf/dnf.conf` 或通过 curl 代理），但这是临时 workaround，不推荐作为正式方案。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 包仓库在 CI 重试时是否已恢复正常服务。
- 如果多次重试仍失败，需确认 `repo.****.org` 是否需要切换镜像源。

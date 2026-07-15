# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2镜像站流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`#8 [builder 2/5] RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像站在 HTTP/2 协议层面发生流错误（stream not closed cleanly: INTERNAL_ERROR），`dnf` 多次重试不同 mirror 均失败，最终所有 mirror 耗尽，`gcc` 包下载失败导致整个 `dnf install` 步骤退出码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 Dockerfile（声明 `dnf install` 需安装的合法包名）、README.md 新行、image-info.yml 新条目和 meta.yml 新映射，不存在任何可能导致远程仓库 HTTP/2 协议错误的代码变更。该失败是 openEuler SP4 仓库镜像站的服务端或中间网络设备的临时性问题。

## 修复方向

### 方向 1（置信度: 高）
**重试即可**。这是 openEuler 24.03-LTS-SP4 软件仓库镜像站的瞬时网络/协议故障（HTTP/2 stream INTERNAL_ERROR），与代码无关。等待仓库服务恢复后重新触发 CI 构建即可。

### 方向 2（可选，置信度: 低）
如果问题持续复现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加 `dnf` 内部重试次数，或回退为 HTTP/1.1（通过设置环境变量 `RPM_CURL_OPTIONS="--http1.1"`）绕过 HTTP/2 协议层问题。但这属于对基础设施问题的临时 workaround，不推荐作为长期方案。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 OS 仓库镜像站（`repo.****.org`）在 CI 失败时间段是否存在已知中断或维护窗口。
- 同一 CI runner（`ecs-build-docker-x86-03-sp`）上同时运行的 `#7 [stage-1 2/4]` 也遇到了同样的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），进一步证实是仓库端问题而非单次网络抖动。
- `#7` 阶段虽然部分包成功重试通过，但最终因为 `#8` 失败而被 BuildKit 取消（`#7 CANCELED`），说明整体构建环境在网络层面确实不稳定。

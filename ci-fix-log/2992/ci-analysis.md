# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, MIRROR, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）在 Docker 构建的 builder 阶段发生 HTTP/2 连接不稳定，多个 RPM 包下载时出现 `Curl error (92): Stream error in the HTTP/2 framing layer`，`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 经过多次镜像重试后仍然失败，导致 `dnf install` 退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据，Dockerfile 语法、包名和构建流程均正确。失败根因是 CI 构建时 openEuler 24.03-LTS-SP4 的官方 RPM 仓库出现 HTTP/2 协议层面的网络故障（服务端或中间网络设备未正常关闭 HTTP/2 流），属于 CI 基础设施/上游仓库的瞬时性问题。

值得注意的是，同一构建中 stage-1（`#7`，运行时阶段的 `dnf install`）也遭遇了相同的 HTTP/2 流错误（`glibc-devel` 和 `gcc-gfortran` 各一次），但最终通过重试成功。builder 阶段（`#8`）下载的包数量更大（157 个 vs 32 个），遭遇多次 HTTP/2 流错误后 `gcc` 包耗尽了所有镜像重试机会。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施/上游仓库的瞬时性网络故障。建议直接重新触发 CI 构建（retry），在仓库网络恢复正常后大概率会通过。

### 方向 2（置信度: 中）
如果多次重试仍然失败，可能是 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务存在持续性问题。此时可以考虑：
- 联系 openEuler 基础设施团队排查仓库 HTTP/2 服务端配置
- 或在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 禁用 HTTP/2，回退到 HTTP/1.1（注：此为降级方案，非推荐做法）

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 RPM 仓库（`repo.****.org`）在本次 CI 构建时段的 HTTP/2 服务健康状态
- 该仓库是否对并发 HTTP/2 连接有速率限制或连接数上限（此次构建中两个 stage 同时从同一仓库批量下载 157+32 个包可能触发了限制）
- 其他使用 openEuler 24.03-lts-sp4 的镜像构建是否也出现了类似失败（可据此判断是否为仓库级系统性故障）

## 修复验证要求
无。此次失败为 infra-error，PR 代码无需修改。若重试后 CI 通过，则验证完成。

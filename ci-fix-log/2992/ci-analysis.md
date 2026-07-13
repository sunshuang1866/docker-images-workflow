# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Repo HTTP/2 流错误
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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 镜像仓库返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），导致 `gcc-12.3.1-110.oe2403sp4.x86_64` 等多个软件包下载重试耗尽后失败。这是仓库服务端的网络/基础设施问题。

### 与 PR 变更的关联
本次 PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 语法和内容本身没有问题。失败完全是由于 openEuler 24.03-LTS-SP4 软件包镜像仓库在 CI 运行时段不稳定，与 PR 代码变更无关。

值得注意的是，运行的 stage-1 阶段（#7，运行时镜像的 `dnf install`）同样遭遇了 `gcc-gfortran` 和 `glibc-devel` 的 HTTP/2 流错误，进一步验证这是仓库侧的共性问题，而非 builder 阶段的独有故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此失败是 openEuler 24.03-LTS-SP4 镜像仓库的临时网络/HTTP/2 协议问题，不是代码缺陷。在仓库恢复稳定后重新触发 CI 构建即可通过。无需修改任何代码。

### 方向 2（置信度: 低）
如果该仓库持续不稳定，可考虑在 Dockerfile 的 `dnf install` 前增加重试逻辑（如 `dnf install --setopt=retries=10 ...`），或配置备用镜像源。但这属于 CI 鲁棒性优化而非当前失败的根因修复。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的软件包镜像仓库（`repo.****.org`）在 CI 运行时段（2026-07-09 14:46 UTC 前后）是否存在已知的 HTTP/2 服务中断或降级。
- 确认同期的其他 SP4 构建 job（同一仓库的其他镜像构建）是否也出现同类失败，以排除 CI runner 本机网络问题。

## 修复验证要求
无需代码修复。验证方式：在仓库恢复稳定后重新触发 CI 构建，确认 builder 阶段的 `dnf install` 能正常下载所有软件包并完成 Docker 镜像构建。

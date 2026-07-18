# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器（`repo.****.org`）在处理 HTTP/2 请求时出现流错误（`INTERNAL_ERROR (err 2)`），多次重试后 `gcc-12.3.1-110.oe2403sp4.x86_64` 包仍无法下载，dnf 耗尽所有可用镜像后报错退出

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容正确（`dnf install` 语法无误，`sed` 编译参数替换规范）。失败发生在 `dnf install` 从远程仓库下载 RPM 包的阶段，此时尚未触及 PR 引入的任何构建逻辑，完全是上游镜像服务器的网络/服务端问题。日志中 `#7`（stage-1 runtime 阶段）和 `#8`（builder 阶段）两个独立阶段均出现了相同类型的 HTTP/2 流错误，进一步证实这是 openEuler 24.03-LTS-SP4 仓库服务器端的问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。此失败属于 CI 基础设施问题，应由运维排查 openEuler 24.03-LTS-SP4 RPM 镜像服务器的 HTTP/2 配置或网络状况。待服务器恢复后，重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
如果 openEuler 24.03-LTS-SP4 镜像服务器频繁出现此类 HTTP/2 流错误，可在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager --setopt=max_retries=10` 增加重试次数，或通过 `dnf install --setopt=retries=10 ...` 提高容错。但这属于绕过而非修复根因，不推荐。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像服务器在构建时间点（2026-07-09 14:46 UTC）是否存在已知的服务中断或 HTTP/2 协议问题
- 该仓库地址（`repo.****.org`，已脱敏）的负载均衡、CDN 或反向代理的 HTTP/2 实现是否有已知缺陷

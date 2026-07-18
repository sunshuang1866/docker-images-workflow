# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, gcc-gfortran, openEuler-24.03-LTS-SP4

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

同时在 stage-1 阶段也出现同类错误：
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）的 HTTP/2 连接异常，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载过程中服务器端 HTTP/2 流未正常关闭（`INTERNAL_ERROR`），经历多次镜像重试后仍全部失败，dnf 无法完成包安装。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个 Dockerfile 及配套的 README、image-info.yml、meta.yml 更新，Dockerfile 中的 `dnf install` 命令语法和包名均正确。构建失败完全由 openEuler 24.03-LTS-SP4 官方软件仓库的 HTTP/2 服务端协议错误导致，属于 CI 基础设施问题，非代码错误。即使回退 PR 变更，在同一时间点重试构建也会遇到同样的网络错误。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库恢复后重试 CI**。错误发生在镜像仓库服务端（`INTERNAL_ERROR` 是服务器返回的 HTTP/2 错误），与 PR 代码无关。可等待 openEuler 软件仓库恢复后重新触发 CI 构建流水线即可通过。

### 方向 2（置信度: 低）
若仓库持续不稳定，可考虑在 Dockerfile 中为 dnf 配置本地镜像源缓存或增加 `--setopt=retries=10` 提高重试次数，但此非根本解决方案。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库在该时间段是否存在已知的 HTTP/2 服务异常或维护公告。
- 同期其他基于 `openeuler:24.03-lts-sp4` 的镜像构建是否也出现同类仓库访问失败。

## 修复验证要求
无需代码修复。Code Fixer 无需处理此 PR。待仓库恢复后重新触发 CI 即可。

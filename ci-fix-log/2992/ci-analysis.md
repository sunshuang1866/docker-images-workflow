# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 下载中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, [MIRROR], [FAILED], No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: CI 构建环境在从 openEuler 24.03-LTS-SP4 仓库镜像站下载 RPM 包时，多次遭遇 HTTP/2 流层错误（Curl error 92：INTERNAL_ERROR），多个包（gcc-gfortran、glibc-devel、guile、gcc）均受影响。gcc 包在所有镜像重试后仍无法成功下载，导致 dnf install 步骤失败。

### 与 PR 变更的关联
PR 变更仅新增了一个标准结构的 Dockerfile（含 `dnf install` 步骤安装构建依赖）及对应的 README/meta.yml 更新。Dockerfile 本身内容无语法错误或逻辑问题。失败的直接原因是 openEuler 24.03-LTS-SP4 软件仓库镜像站的 HTTP/2 连接不稳定，属于 CI 基础设施网络问题，**与 PR 代码变更无关**。

值得注意的是，构建日志中 `#7`（stage-1，运行时阶段）和 `#8`（builder，编译阶段）两个独立构建阶段都在访问同一 SP4 仓库时出现了相同的 HTTP/2 流错误，说明这是仓库侧的普遍性问题，而非单次偶发网络抖动。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是 openEuler 24.03-LTS-SP4 软件仓库镜像站的临时性 HTTP/2 服务问题（Curl error 92），与 PR 代码无关。等待仓库恢复后重新触发 CI 构建即可。如果持续失败，需联系 openEuler 基础设施团队排查 SP4 仓库镜像站的 HTTP/2 服务稳定性。

### 方向 2（置信度: 低）
**降级 HTTP/1.1 规避**。如果 SP4 仓库的 HTTP/2 实现持续不稳定，可在 Dockerfile 的 `dnf install` 前通过设置 `DNF` 或 `libcurl` 环境变量强制使用 HTTP/1.1（如 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `CURL_HTTP_VERSION` 环境变量），绕过 HTTP/2 流层问题。但这只是临时规避手段，根本原因在仓库侧。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org`）当时的服务状态，是否存在已知的 HTTP/2 服务中断或降级。
- 同一时间段其他使用 SP4 仓库的 PR 构建是否也出现了相同的 Curl error 92，以确认这是仓库侧的系统性问题还是个别 runner 的网络问题。

## 修复验证要求
此失败为 infra-error，无需代码修复。若选择方向 2 进行规避，Code Fixer 需验证 Dockerfile 构建在 openEuler 24.03-LTS-SP4 容器中 `dnf install` 能够稳定完成。

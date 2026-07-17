# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, MIRROR, FAILED, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

同步地，第二个构建阶段 `#7 [stage-1 2/4]` 也遭遇同类错误：
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在通过 HTTP/2 协议传输大型 RPM 包（gcc 34MB、gcc-gfortran 13MB、glibc-devel 2MB、guile 6.3MB）时频繁出现 `Curl error (92)` HTTP/2 stream 中断错误，`dnf` 尝试所有镜像均失败后退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个遵循已有 sp3 模式的标准 Dockerfile（及其只读元数据），Dockerfile 中 `dnf install` 命令语法完全正确，`sed` 补丁与 sp3 版本一致。失败根因是 CI 构建时 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 传输层出现故障，两个并发构建阶段（#7 和 #8）同时受同一仓库镜像影响，进一步确认这是仓库侧基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**等仓库恢复后重试触发 CI。** 这是 openEuler 24.03-LTS-SP4 软件仓库镜像的临时性 HTTP/2 协议故障，与 PR 代码无关。等待仓库运维方修复 HTTP/2 服务后，重新触发 CI 构建（re-run）即可通过。

### 方向 2（置信度: 低）
**若续发失败，在 Dockerfile 中降级 dnf 的 HTTP 协议。** 如果 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务存在持续性问题，可在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置环境变量强制 curl/libcurl 回退到 HTTP/1.1。但此方向应当仅在仓库确认无法修复 HTTP/2 问题时采用，且需要 upstream openEuler 仓库管理员的确认。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org/openEuler-24.03-LTS-SP4/`）的 HTTP/2 服务状态，确认是否为临时性故障。
2. 其他引用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也遭遇同类 Curl error (92) 失败——如果是，则进一步确认是仓库侧系统性问题。
3. 若重试多次持续失败，需确认仓库是否已弃用 HTTP/2 或存在特定的 HTTP/2 连接限制策略。

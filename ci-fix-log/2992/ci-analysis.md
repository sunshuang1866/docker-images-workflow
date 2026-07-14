# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2连接异常
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误

```
#8 [builder 2/5] RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all
...
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all" did not complete successfully: exit code: 1
```

`#7`（final stage）也出现了同类错误并被取消：
```
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer... [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 CANCELED
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方包仓库（`repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/`）的 HTTP/2 服务端存在协议实现问题，在传输大体积 RPM 包（如 gcc 34MB、gcc-gfortran 13MB）时频繁发生 `Stream error in the HTTP/2 framing layer`（Curl errno 92），经 `dnf` 多次换 mirror 重试后所有镜像均失败，最终导致 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了 `openEuler 24.03-lts-sp4` 版本的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 安装的均为 openEuler 官方仓库中的标准包，无自定义仓库或网络配置。本次失败是 openEuler SP4 包仓库的 HTTP/2 基础设施问题，属于 transient/临时性的 infra-error。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。这是 openEuler 24.03-LTS-SP4 包仓库的 HTTP/2 协议临时性故障，与 PR 代码无关。等待仓库侧 HTTP/2 服务恢复后，重新运行 CI 流水线即可通过。

### 方向 2（置信度: 低，仅当方向 1 反复失败时考虑）
若多次重试后相同错误持续出现，可尝试在 Dockerfile 中为 `dnf` 追加 `--setopt=retries=10` 提高重试容忍度，或临时切换为 HTTP/1.1 协议（如在 dnf 配置中禁用 HTTP/2）。但这类 workaround 不应作为长期方案，根本问题仍需 repo 服务端解决 HTTP/2 协议兼容性。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 包仓库的 HTTP/2 协议兼容性是否为已知问题（可向 openEuler infra 团队确认）
- 该仓库问题是否影响所有 openEuler SP4 的镜像构建（可检查同期其他 SP4 PR 的 CI 运行结果交叉验证）

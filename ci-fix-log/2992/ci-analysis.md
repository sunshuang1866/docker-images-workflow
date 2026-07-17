# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: repo镜像HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo.***.org

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 repo 镜像服务器在处理 HTTP/2 请求时频繁返回 `INTERNAL_ERROR (err 2)`，导致多个大型 RPM 包（gcc-gfortran 13MB、glibc-devel 2MB、guile 6.3MB、gcc 34MB）下载中断。部分包通过重试成功下载，但 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34MB）在耗尽所有镜像重试后仍失败，导致 dnf 安装整体失败。

### 与 PR 变更的关联

**与 PR 代码变更无关。** 该 PR 仅新增了一个 Dockerfile（以及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 语法和内容完全正确。失败根因是 openEuler 24.03-LTS-SP4 repo 镜像服务器的 HTTP/2 协议实现缺陷——服务器端发送了 `INTERNAL_ERROR` 导致 HTTP/2 stream 异常关闭，属于 CI 基础设施问题。构建环境中的 Stage-1（运行时阶段）在下载同一 repo 的包时也遇到了完全相同的 `Curl error (92)` 错误，进一步证明这是 repo 镜像端的系统性故障，而非 Dockerfile 问题。

## 修复方向

### 方向 1（置信度: 低）
**重试构建**：HTTP/2 stream error 为 repo 镜像服务器的间歇性故障，可能仅在特定时间段发生。等待镜像服务器恢复后重新触发 CI 构建即可。

### 方向 2（置信度: 低）
**降级为 HTTP/1.1**：在 Dockerfile 的 `dnf install` 前配置 curl 使用 HTTP/1.1 协议（`echo "http1" >> /etc/dnf/dnf.conf` 或设置 `ip_resolve=4` 等），绕过 repo 镜像的 HTTP/2 实现缺陷。但此方案属于规避而非修复，且不确定 dnf 内嵌的 libcurl 是否支持此参数。

## 需要进一步确认的点

1. openEuler 24.03-LTS-SP4 repo 镜像服务器的 HTTP/2 配置是否存在已知问题，需联系镜像站运维确认
2. 该 repo 镜像的 HTTP/2 错误是否为间歇性（确认后可直接重试）还是持续性（需要运维修复）
3. 同一时间段内，其他依赖 openEuler 24.03-LTS-SP4 repo 的 PR 是否也遇到相同错误——如果普遍出现，则确认为基础设施问题
4. 该镜像仓库 URL 的具体域名（日志中已脱敏为 `repo.****.org`）——需确认是否为 openEuler 官方仓库还是内部镜像代理

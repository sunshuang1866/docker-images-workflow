# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库（`repo.****.org`）在本次构建期间出现 HTTP/2 协议层传输异常（`Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`），多个包（cmake-data、git-core、gcc-c++）先后遭遇相同错误。虽然 dnf 的重试机制使大部分包最终成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64` 在两次 HTTP/2 流中断重试后耗尽了所有镜像地址，下载彻底失败，导致整个 `dnf install` 命令返回 exit code 1。

### 与 PR 变更的关联
**无关。** 该 PR 仅新增一个 grads 2.2.3 的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确、包名列表与同类 `24.03-lts-sp4` 镜像一致。失败根因是 openEuler 上游 RPM 仓库镜像的 HTTP/2 协议临时异常，属于 CI 基础设施问题，与 PR 代码变更无任何因果关联。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 本次失败为 openEuler 软件仓库镜像的 HTTP/2 协议临时故障，属于瞬态 infra-error。该仓库在多个 PR 构建中同时提供服务，此类偶发性的 HTTP/2 流中断通常会自行恢复。建议：在 Jenkins 上重新触发一次构建（retry/re-build），大概率可通过。

### 方向 2（置信度: 低）
若多次重试仍失败，可能说明 `repo.****.org` 的特定 CDN/镜像节点存在持续性 HTTP/2 兼容性问题。此时可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 协议下载，绕过 HTTP/2 层问题。但此方向仅作为持续失败时的备选方案，当前证据不充分，不建议主动修改代码。

## 需要进一步确认的点
- `repo.****.org`（被脱敏掩码的 openEuler 软件仓库域名）的实际地址及该镜像站点的当前健康状态
- 该构建节点（`ecs-build-docker-x86-03-sp`）到该仓库的网络链路是否稳定
- 该仓库是否近期升级了 HTTP/2 配置导致与特定 curl 版本不兼容

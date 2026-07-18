# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误

```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: Docker 构建过程中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，HTTP/2 协议层反复出现 `INTERNAL_ERROR`（Curl error 92），导致 gcc-c++ 等包下载失败（所有镜像均重试失败），整个 `dnf install` 步骤以 exit code 1 终止。此前 cmake-data 和 git-core 包也出现了相同的 HTTP/2 流错误，但经重试后成功下载。

### 与 PR 变更的关联
**无关。** 该 PR 仅新增了 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套的 README、image-info.yml、meta.yml 条目。Dockerfile 中 `dnf install` 所列的包均为合法存在的 openEuler 仓库包名（其中大部分包已在该次构建中成功下载，如 gcc、cmake、git-core 等）。失败本质上是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端存在问题，导致部分下载流被非正常关闭。PR 代码变更不会触发此错误。

## 修复方向

### 方向 1（置信度: 中）
**重试构建。** 该错误属于 CI 基础设施的瞬时网络问题（仓库镜像 HTTP/2 流异常），与 PR 代码无关。建议在 CI 中重新触发该 job，通常重新构建即可成功。若多次重试仍复现同一错误，则说明 openEuler 24.03-LTS-SP4 仓库镜像存在持续性问题，需联系镜像站运维排查 HTTP/2 服务端配置。

## 需要进一步确认的点
- 确认该仓库镜像（`repo.****.org`）在构建时段是否存在已知的 HTTP/2 服务端异常或负载过高问题。
- 若重试 3 次以上仍失败，需确认该镜像站对 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 支持和稳定性是否已降级。
- 是否有同类 PR（基于 `openeuler:24.03-lts-sp4` 基础镜像构建）在同一时段也出现了相同的 dnf 下载错误，以判断是全局性仓库问题还是仅针对特定包/时间段。

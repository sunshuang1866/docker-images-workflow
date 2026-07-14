# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件仓库镜像（`repo.****.org`）在 HTTP/2 传输层反复出现 `INTERNAL_ERROR (err 2)` 流错误，导致 `gcc-c++` 等 RPM 包下载失败。`dnf` 尝试了所有可用镜像后仍然无法完成下载，构建在包安装阶段失败。

此外，日志中 `cmake-data` 和 `git-core` 两个包也曾触发过相同的 HTTP/2 流错误（分别发生在 stream 15 和 stream 75），虽然它们最终通过重试下载成功，但 `gcc-c++`（13MB）在两个不同 stream 上均失败，最终耗尽所有镜像重试机会。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile 和配套的元数据文件，Dockerfile 中的 `dnf install` 命令格式与同类镜像完全一致，语法正确。失败完全由 openEuler 软件仓库镜像服务器的 HTTP/2 协议层问题导致，属于 CI 基础设施层面的瞬时故障。该镜像此前可能未在 24.03-lts-sp4 上构建过（本次为首次新增），因此相比已有镜像更容易暴露仓库不稳定问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是一个 CI 基础设施/上游仓库镜像的网络问题（HTTP/2 stream error），与 Dockerfile 内容无关。建议等待仓库镜像恢复后重试 CI，或联系 openEuler 基础设施团队排查 `repo.****.org` 的 HTTP/2 服务稳定性。

## 需要进一步确认的点
- 日志中镜像仓库域名被脱敏（`repo.****.org`），无法直接判断具体是哪个镜像站。若问题持续复现，建议确认实际仓库地址并检查其 HTTP/2 配置。
- 观察相同仓库的其他 PR 构建是否也出现类似 HTTP/2 流错误，以判断是偶发还是持续性故障。

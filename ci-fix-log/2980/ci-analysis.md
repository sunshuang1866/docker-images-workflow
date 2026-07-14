# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 镜像流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在通过 HTTP/2 协议传输 `gcc-c++` RPM 包时发生流层错误（Curl error 92），dnf 重试所有可用镜像后均失败，导致依赖安装中断。此外 `cmake-data` 和 `git-core` 也出现了同样的 HTTP/2 流错误但重试成功。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 本身语法和内容没有问题（`dnf install` 命令格式正确、依赖列表合理），失败纯粹由 CI 构建时 openEuler 24.03-LTS-SP4 软件包仓库镜像的 HTTP/2 服务端异常导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 CI 基础设施侧的开源软件包仓库镜像端 HTTP/2 服务异常，属于临时性网络/服务端问题。建议触发重新构建（retry），仓库镜像恢复后即可通过。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 软件包仓库）的 HTTP/2 服务是否已恢复正常
- 如果多次 retry 后仍持续出现此错误，考虑在 CI 构建脚本中为 dnf 配置 `http2=false` 降级为 HTTP/1.1，或更换更稳定的镜像站
- 该问题可能影响所有使用 openEuler 24.03-LTS-SP4 基础镜像的 Dockerfile 构建，需关注是否有其他 PR 也遭遇同类失败

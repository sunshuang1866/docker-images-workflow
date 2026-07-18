# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境从 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库镜像）下载 RPM 包时，多个包遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`。其中 `cmake-data` 和 `git-core` 在重试后下载成功，但 `gcc-c++`（13 MB 大包）两次遭遇 HTTP/2 流错误后耗尽所有 mirror 重试次数，最终 dnf 安装失败。该错误是 openEuler 仓库镜像服务器或中间网络代理的 HTTP/2 协议层瞬态故障，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 的改动是新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中 `dnf install` 的包名列表正确，均为 openEuler 24.03-LTS-SP4 仓库中的合法包名（日志中 dnf 已成功解析依赖并列出 258 个待安装包）。失败纯粹由仓库镜像的 HTTP/2 通信异常导致，与 PR 代码变更**无直接关联**。

## 修复方向

### 方向 1（置信度: 中）
该错误为 CI 基础设施/网络瞬态故障，建议直接**重试 CI 构建**。openEuler 仓库镜像的 HTTP/2 流错误通常为间歇性服务器端或代理问题，多次重试后大概率可以通过。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
若重试多次仍然失败，可能需要在 CI 构建节点上禁用 HTTP/2（强制使用 HTTP/1.1）来绕过仓库镜像的 HTTP/2 协议层问题。这需要修改 CI runner 的 dnf/yum 配置（如 `/etc/dnf/dnf.conf` 中添加 `http2=false` 或通过 `--setopt` 传递），属于 CI 基础设施层面的调整，不在 Dockerfile 代码修改范围内。

## 需要进一步确认的点
1. 重试 CI 构建 2-3 次，观察该错误是否持续复现。若为间歇性问题，确认修复方向 1 即可。
2. 若持续复现，需排查 `repo.****.org`（openEuler 24.03-LTS-SP4 镜像源）的 HTTP/2 服务端健康状况，或检查 CI 构建节点与镜像源之间的网络代理/负载均衡器是否对 HTTP/2 长连接有不当处理。
3. 确认其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也遇到同类错误——若大量发生则为系统性镜像源问题。

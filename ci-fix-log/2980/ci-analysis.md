# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, dnf install, gcc-c++

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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方软件仓库镜像在 HTTP/2 传输层发生流错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等多个 RPM 包下载失败。DNF 重试所有可用镜像后仍失败，最终退出码为 1。这是 CI 构建环境与 `repo.*.org` 镜像站之间的网络基础设施问题。

### 与 PR 变更的关联
PR #2980 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，该文件通过 `dnf install` 安装编译依赖。`dnf install` 命令本身是正确的——DNF 成功解析了所有 258 个依赖包的列表，实际下载过程也正常启动了大部分包（`git-core`、`cmake-data` 等在重试后成功下载）。唯一的失败点是 `gcc-c++` 包在 HTTP/2 流错误重试后仍然失败。该失败与 PR 代码改动无关，属于仓库镜像站的网络传输稳定性问题。

## 修复方向

### 方向 1（置信度: 低）
**触发重新构建**。HTTP/2 流错误通常是临时的服务端或 CDN 问题，重新运行 CI 可能直接通过。无需修改 Dockerfile。

### 方向 2（置信度: 低）
**更换 DNF 镜像源**。如果该仓库镜像持续存在 HTTP/2 问题，可在 `dnf install` 前添加 `dnf config-manager --setopt` 切换到备用镜像站，或使用 HTTP/1.1 降级传输（`curl` 和 `dnf` 默认使用 HTTP/2，可尝试禁用以绕过该问题）。但日志中已有多个镜像被尝试（`All mirrors were already tried`），说明 DNF 已自动切换到备用镜像，复用性有限。

## 需要进一步确认的点
1. `repo.*.org`（日志中已脱敏）的实际域名和当前的 HTTP/2 服务状态——是临时故障还是 24.03-LTS-SP4 仓库的 HTTP/2 一直不稳定？
2. 该仓库是否有 HTTP/1.1 fallback 机制？DNF/libcurl 在触发此错误后是否尝试过降级到 HTTP/1.1？
3. 其他 24.03-LTS-SP4 的镜像构建（同批次或近期其他的 SP4 Dockerfile 构建）是否也出现类似的 HTTP/2 流错误？如果普遍存在，说明是仓库侧的系统性问题；如果仅此一例，说明是临时网络波动。

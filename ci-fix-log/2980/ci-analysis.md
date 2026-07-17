# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2连接异常
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR (err 2)`, `No more mirrors to try`, `All mirrors were already tried without success`

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像站在 HTTP/2 传输层出现间歇性流错误（`Curl error 92`），导致 `cmake-data`、`git-core`、`gcc-c++` 三个包下载失败。其中 `cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++` 包两次下载均失败且所有镜像均已尝试，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个新的 `24.03-lts-sp4` Dockerfile，其 `dnf install` 命令中列出的依赖包列表与 `24.03-lts-sp3` 版本的同类 Dockerfile 在内容和格式上完全一致（标准的开发工具链和图形库依赖）。失败是由 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 传输层间歇性异常引起的网络问题，属于外部基础设施故障。

## 修复方向

### 方向 1（置信度: 中）
这是一个网络/基础设施层面的瞬态故障，通常重试即可恢复。最简方案是触发 CI 重新运行（retry），观察问题是否自愈。若重试后仍失败，则考虑方向 2。

### 方向 2（置信度: 低）
若多次重试仍失败，可在 Dockerfile 的 `dnf install` 命令中追加 `--setopt=retries=10 --setopt=timeout=120` 等重试参数，或通过 `echo "http2=false" >> /etc/dnf/dnf.conf` 在安装前禁用 HTTP/2 回退到 HTTP/1.1，以规避 HTTP/2 流错误。但需注意这仅是对上游基础设施问题的临时规避，不应作为首选方案。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org`）在构建时间点（2026-07-13 07:04）的 HTTP/2 服务健康状况是否正常，是否存在已知故障或维护窗口。
2. CI 构建环境到 `repo.****.org` 之间的网络链路是否存在代理/防火墙干扰 HTTP/2 长连接的情况。
3. 同样使用该仓库的其他 24.03-lts-sp4 Dockerfile 构建 job 在同一时间段是否也出现类似网络错误（可据此判断是特例还是广域问题）。

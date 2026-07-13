# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像站 (`repo.****.org`) 在 HTTP/2 协议层面出现间歇性流错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载中断。其中 cmake-data 和 git-core 通过重试成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（13 MB）在多次重试后仍失败，耗尽所有镜像，最终导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了一个结构正确的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及对应的元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确，包名列表与同类镜像一致。失败根因是 openEuler 仓库镜像站的 HTTP/2 服务端协议异常，属于基础设施问题，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**等待镜像站恢复后重试构建。** 该错误为 openEuler 仓库镜像站（`repo.****.org`）的 HTTP/2 服务端间歇性问题，与 PR 代码无关。建议等待镜像站维护方修复 HTTP/2 流处理问题后，重新触发 CI 构建。

### 方向 2（置信度: 低）
如果镜像站长期未恢复，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `--setopt=ip_resolve=4` 等 dnf 参数，强制使用 HTTP/1.1 协议降级下载，绕过 HTTP/2 流错误。但此改动属于临时 workaround，不建议作为正式修复方案提交。

## 需要进一步确认的点
1. 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 官方仓库镜像）当前 HTTP/2 服务是否已恢复正常。
2. 确认同一时间段其他 SP4 版本的镜像（如 `Others/grads/2.2.3/24.03-lts-sp3/Dockerfile`）是否也出现类似下载失败——若仅 SP4 仓库受影响，说明问题仅限 SP4 源；若多版本仓库均受影响，可能是整体镜像站故障。
3. 确认该 CI runner（`ecs-build-docker-x86-03-sp`）与仓库镜像站之间的网络链路是否存在问题。

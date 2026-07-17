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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: 在 `dnf install` 下载软件包阶段，openEuler 24.03-LTS-SP4 仓库镜像站持续返回 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`）。其中 `cmake-data` 和 `git-core` 在重试后下载成功，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm`（约13MB）经历两次 HTTP/2 流错误后所有镜像均耗尽，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及其配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法正确，软件包名均合法——DNF 成功解析了依赖关系并确定了 258 个待安装包的列表。失败完全发生在 RPM 包下载阶段，由 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 传输层问题导致，属于基础设施层面的网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是一个基础设施层面的临时网络问题（openEuler 仓库镜像站 HTTP/2 流传输不稳定），与 PR 的代码变更无关。等待镜像站恢复后重新运行 CI 流水线即可。如果问题反复出现，可考虑在 Dockerfile 中为 `dnf install` 增加 `--retries` 参数或设置 `ip_resolve=4` 的 curl 配置，降低 HTTP/2 协议层面的不稳定性影响。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org`）在 CI 构建时间段（2026-07-13 07:04 UTC 前后）是否存在 HTTP/2 服务波动或负载异常
- 如果该镜像站持续出现 HTTP/2 流错误，可能需要 CI 运维团队检查镜像站健康状况或更换备用镜像源
- 验证同一时段内其他基于 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也遇到了类似的 DNF 下载失败，以确认是系统性还是偶发问题

## 修复验证要求
无需特殊验证。此失败为 infra-error，re-trigger CI 后如果构建成功即表明问题已自行恢复。若重试后仍失败，需进一步排查镜像站状态。

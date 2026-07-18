# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在处理 HTTP/2 请求时频繁出现 `INTERNAL_ERROR (err 2)` 帧层错误，导致 `cmake-data`、`git-core`、`gcc-c++` 等多个包的下载中断。gcc-c++ 包在两次重试（stream 65 和 stream 83）均失败后耗尽所有镜像。最终 dnf 因无法完成 gcc-c++ 的下载而退出（exit code: 1）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及配套的 README、image-info.yml、meta.yml 元数据文件。Dockerfile 中的 `dnf install` 命令语法正确、包列表完整（依赖解析阶段已成功列出了 258 个待安装包），构建失败纯粹因为 openEuler 24.03-LTS-SP4 仓库镜像在构建时出现 HTTP/2 协议层传输故障。Dockerfile 代码本身无需修改。

## 修复方向

### 方向 1（置信度: 中）
**重试触发 CI**。该错误为仓库镜像的瞬时网络故障（HTTP/2 帧层内部错误），部分包（如 gcc 34MB）已成功下载，仅有 gcc-c++ 等少数包在多次重试后仍失败。重新触发 CI 构建有一定概率成功（镜像服务恢复后）。建议等待一段时间后 retry。

### 方向 2（置信度: 低）
**dnf 配置绕过 HTTP/2 或切换镜像站**。如果该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 问题是持续性的，可在 Dockerfile 的 `dnf install` 前添加 dnf 配置步骤：
- 通过 `/etc/dnf/dnf.conf` 或 `--setopt` 禁用 HTTP/2（如 `--setopt=ip_resolve=4` 等）
- 或切换为不同的软件源镜像（如 `repo.huaweicloud.com` 对应的 openEuler 24.03-LTS-SP4 源）

但由于仅此一次构建失败，难以判断是瞬时还是持续性问题，证据不足以确认需要此修复。

## 需要进一步确认的点
1. **该仓库镜像的 HTTP/2 问题是否为持续性的**：查看同时间段内其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建是否也出现相同的 Curl error (92)，以判断是瞬时故障还是服务器端配置问题。
2. **是否需要多架构验证**：该 PR 声明支持 `amd64, arm64`，当前提供的日志仅为 x86-64 构建。需确认 aarch64 构建是否也遇到了同样的镜像下载问题。
3. **仓库镜像管理员确认**：联系 `repo.****.org` 的运维团队确认 24.03-LTS-SP4 仓库的 HTTP/2 服务状态是否正常。

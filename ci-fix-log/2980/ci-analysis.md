# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器（`repo.****.org`）在 Docker 构建期间发生 HTTP/2 帧层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 包多次下载失败，最终所有镜像尝试均耗尽，dnf 安装失败。

日志中另有 `cmake-data` 和 `git-core` 两个包也遭遇了同类 HTTP/2 流错误，但它们在重试后成功下载。`gcc-c++` 则重试失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。该 PR 仅新增了一个标准格式的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`），其 `dnf install` 包列表语法正确、包名合法，与同仓库中其他 GrADS Dockerfile（如 `24.03-lts-sp3` 版本）的依赖安装方式一致。失败完全由 CI 构建时 openEuler 仓库镜像服务器的临时网络故障引起。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重新构建。** 根因是 openEuler 仓库镜像服务器的临时 HTTP/2 协议故障，与 PR 代码无关。等待仓库镜像恢复后重新触发 CI 流水线即可。建议在重新触发前验证仓库 `https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/` 的连通性和 HTTP/2 稳定性。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库镜像服务器是否已恢复正常服务。
- 若重新触发后仍然失败，检查是否需要更换或添加备用镜像源（如 `mirrors.tuna.tsinghua.edu.cn` 等），但这是 CI 基础设施层面的调整，不属于本次 PR 修改范围。

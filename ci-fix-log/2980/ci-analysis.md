# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像存在 HTTP/2 传输层问题，导致多个 RPM 包下载过程中出现 Curl error (92)（HTTP/2 stream 未正常关闭），其中 `gcc-c++` 包两次重试均失败，所有镜像均已尝试完毕，dnf 无法完成安装。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 此次 PR 仅新增了 4 个文件：Dockerfile（含标准 `dnf install` 命令）、README.md 条目、image-info.yml 条目、meta.yml 条目。Dockerfile 中的 `dnf install` 命令语法和包名均正确（日志中 `Dependencies resolved` 阶段列出了全部 258 个包，依赖解析成功）。失败纯粹是因为 CI 构建环境访问 openEuler 24.03-LTS-SP4 仓库镜像时遭遇 HTTP/2 流错误，属于基础设施层面的临时网络问题。

值得注意的是：`cmake-data` 和 `git-core` 同样遭遇了 HTTP/2 流错误，但重试后下载成功；唯有 `gcc-c++`（13 MB）两次尝试均失败，耗尽所有镜像。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该错误为基础设施/网络临时故障，HTTP/2 流错误（Curl error 92）具有间歇性特征。PR 中的 Dockerfile 代码本身没有问题，重新运行 CI pipeline 大概率可以通过。

## 需要进一步确认的点
- 该错误仅在本次 x86_64 架构构建中出现。如果 aarch64 架构的构建也同时失败，需确认其具体错误信息是否同为 HTTP/2 流错误。
- 建议确认 openEuler 24.03-LTS-SP4 仓库镜像服务在 CI 触发时段是否有已知的 HTTP/2 服务端问题。

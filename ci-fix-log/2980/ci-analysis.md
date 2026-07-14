# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6-16（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在 HTTP/2 传输层出现服务器端 `INTERNAL_ERROR`（err 2），导致 `curl` 下载 RPM 包时流被异常关闭。经过多次重试后，`gcc-c++` 包仍无法从任何镜像下载成功，dnf 安装步骤失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该失败是 CI 构建环境与 openEuler 软件仓库之间的网络/服务器端协议层故障。PR 仅新增了一个符合规范的 Dockerfile、更新了 README.md、image-info.yml 和 meta.yml，其中 `dnf install` 命令的包列表和语法均与项目中其他 24.03-lts-sp4 的 Dockerfile 一致，不存在代码层面导致此故障的可能。

## 修复方向

### 方向 1（置信度: 高）
**等待并重试。** 这是 openEuler 仓库镜像站的临时性 HTTP/2 服务端故障，与 PR 代码无关。Code Fixer 无需对 Dockerfile 做任何修改。在仓库服务恢复后重新触发 CI 构建即可。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像 `repo.****.org` 当时的服务状态是否正常（是否存在 HTTP/2 协议层 bug 或临时过载）。
- 如果多次重试后问题持续复现，可确认是否为仓库服务器端持续的 HTTP/2 兼容性问题，考虑联系 openEuler 基础设施团队排查。

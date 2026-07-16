# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像（`repo.****.org`）在 Docker 构建期间出现 HTTP/2 协议层面的流连接异常（curl error 92: HTTP/2 stream INTERNAL_ERROR），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载时 HTTP/2 流被服务端非正常关闭。其中 `gcc-c++-12.3.1-110.oe2403sp4.x86_64` 在重试所有可用镜像后仍然下载失败，`dnf install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的改动仅为：
1. 新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（30 行新增，标准 `dnf install` + `git clone` + `autoreconf` + `make` 流水线）
2. 更新 README.md、image-info.yml、meta.yml 的文档/元数据条目

Dockerfile 本身没有语法错误或逻辑缺陷——日志显示 `dnf` 成功解析了 258 个包的依赖关系并开始了下载（前 17 个包下载成功，如 acl、automake、brotli-devel 等），部分大型包（如 gcc 34MB）也下载成功。失败原因纯粹是远程仓库服务器端的 HTTP/2 协议故障，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是临时性的基础设施问题——仓库镜像服务器的 HTTP/2 连接不稳定是瞬态的。同一 Dockerfile 在其他时段重试大概率能正常完成构建。该 PR 的代码变更无需任何修改。

### 方向 2（置信度: 中）
如果问题持续多天反复出现，需要 CI 基础设施团队介入排查：
- 检查构建节点与 `repo.****.org` 之间的网络链路是否存在 HTTP/2 协议兼容性问题
- 考虑在构建节点上配置 `curl` 降级为 HTTP/1.1（通过 `~/.curlrc` 设置 `--http1.1`）或调整 dnf 的镜像源优先级

## 需要进一步确认的点
- 同一时段其他 PR 的 24.03-LTS-SP4 构建是否也出现相同错误（用于确认是否为仓库侧全局问题）
- 该仓库镜像是否存在历史 HTTP/2 稳定性问题（用于判断是否需要切换到备用镜像源）

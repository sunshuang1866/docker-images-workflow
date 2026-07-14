# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` RUN 指令）
- 失败原因: CI 构建环境从 openEuler 24.03-LTS-SP4 仓库 (`repo.****.org`) 下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）的 HTTP/2 传输流被异常关闭（`Curl error (92): Stream error in the HTTP/2 framing layer, INTERNAL_ERROR`），`gcc-c++` 重试后所有镜像均耗尽，最终无法完成下载。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及相关元数据文件，`dnf install` 中列出的包名均正确且是构建 GrADS 2.2.3 所需的合理依赖。失败的直接原因是 openEuler 24.03-LTS-SP4 仓库镜像在构建时的 HTTP/2 连接层存在间歇性故障，导致大文件（`gcc-c++` 13MB、`git-core` 11MB、`cmake-data` 2.1MB）下载过程中流被异常中断。小文件（如 `acl` 51kB、`automake` 462kB 等）下载均成功。

## 修复方向

### 方向 1（置信度: 高）
**重试即可。** 这是 CI 基础设施/仓库网络的暂时性问题，Dockerfile 本身无需修改。等待仓库镜像 HTTP/2 问题恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
如果此类 HTTP/2 错误频繁复现，可在 Dockerfile 的 `dnf install` 命令前添加配置禁用 HTTP/2 回退到 HTTP/1.1（如 `echo "http2=false" >> /etc/dnf/dnf.conf`），或为 dnf 添加 `--setopt=retries=10` 增加重试次数。但这属于绕过基础设施问题，不推荐作为首选方案。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像 (`repo.****.org`) 在构建时段是否存在已知的 HTTP/2 服务问题
- 确认该错误是否为偶发（可重试通过）还是高概率复现（需调整连接策略）

# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 仓库镜像出现 HTTP/2 协议层面的流中断错误（Curl error 92），导致多个 RPM 包（git-core、gcc-c++、guile）下载失败。其中 `guile` 包耗尽所有镜像重试后下载仍失败，最终 `dnf` 命令退出码为 1。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 vvenc Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install` 命令格式正确、无语法错误。失败根源是 `repo.openeuler.org` 仓库服务器的 HTTP/2 连接在 aarch64 构建期间不稳定，为瞬时基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 CI 基础设施中的瞬时网络问题（openEuler 官方 RPM 仓库的 HTTP/2 服务端在下载时段出现流错误）。直接重新触发 CI 构建，大概率可以成功通过。若重试后仍然失败，可联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端配置或负载均衡问题。

## 需要进一步确认的点
- 重新触发 CI 后是否恢复正常（预期是）。
- 若多次重试仍失败，需确认 `repo.openeuler.org` 的 HTTP/2 服务端是否有已知问题或维护窗口。
- aarch64 runner 所在网络到 `repo.openeuler.org` 的链路是否存在波动（可从 runner 端手动 `curl` 测试验证）。

## 修复验证要求
无需填写（infra-error，由基础设施团队而非 code-fixer 处理）。

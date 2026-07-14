# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（新增文件）
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install -y git gcc gcc-c++ make cmake` 时，`repo.openeuler.org` 仓库服务器对多个 RPM 包（git-core、gcc-c++、guile）返回 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)`），其中 `guile` 包在多次重试后仍失败，dnf 耗尽所有镜像重试次数后报错退出。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅为新增 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中 `dnf install` 的命令语法和包名均正确，失败纯粹由 `repo.openeuler.org` 仓库服务器端 HTTP/2 协议层不稳定导致，属于 CI 基础设施/网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 该失败为 `repo.openeuler.org` 镜像仓库服务器端 HTTP/2 流中断导致的临时性网络故障。建议 CI 运维人员排查 `repo.openeuler.org` 的 HTTP/2 服务端稳定性，或等待网络恢复后重试构建。若问题持续，可考虑在 Dockerfile 的 `dnf install` 前添加重试机制：

1. 将 `dnf install` 包装在重试循环中（如 `for i in 1 2 3; do dnf install ... && break; done`），以容忍临时性 HTTP/2 流错误
2. 或在 `dnf install` 前设置 `echo 'retries=10' >> /etc/dnf/dnf.conf` 增加 dnf 内置重试次数

### 方向 2（置信度: 低）
若上述临时性故障排除后仍失败，需排查 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库中 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 等包是否真实存在且可正常访问（排除包缺失或路径错误）。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 HTTP/2 服务端稳定性状态——是否为已知间歇性故障
2. 其他同时期针对 `24.03-lts-sp4` 的 PR 构建是否也遇到类似 HTTP/2 流错误（判断是全局问题还是个别 runner 的网络问题）
3. 在相同 aarch64 runner 上手动 curl 或 wget 下载 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 验证服务端是否已恢复

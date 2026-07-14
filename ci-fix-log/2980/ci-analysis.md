# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, openEuler repo

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 层在传输 RPM 包时反复出现流错误（`INTERNAL_ERROR (err 2)`），其中 `cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++`（13MB）两次重试均失败，最终 dnf 无可用镜像而中止。这是仓库端 HTTP/2 实现的瞬态故障，与 PR 代码无关。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 包列表完整且符合 openEuler 包命名规范。失败纯粹是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 传输层在 CI 运行时段出现不稳定，导致部分大型 RPM 包下载失败。已有同类包重试成功（cmake-data 16MB 重试后成功），说明仓库本身可访问但连接不稳定。

## 修复方向

### 方向 1（置信度: 高）
**重试即可。** 这是 CI 基础设施层的瞬态网络故障（repo 端 HTTP/2 流错误），非代码缺陷。等待仓库端恢复后重新触发 CI 构建即可通过。Code Fixer 无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 低）
如果该仓库长期存在 HTTP/2 不稳定问题（多次重试仍失败），可在 Dockerfile 的 `dnf install` 命令前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制降级到 HTTP/1.1，或添加 `--retries 10` 增加 dnf 重试次数以提高容错性。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 openEuler 24.03-LTS-SP4 仓库是否在 CI 运行时段存在已知的 HTTP/2 服务不稳定问题。
- 确认同一时段其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也出现类似的 dnf 下载失败。如果是，则进一步确认是仓库端问题。

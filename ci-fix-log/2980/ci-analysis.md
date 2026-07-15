# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, not closed cleanly, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库在本次构建中多次出现 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR），cmake-data 和 git-core 重试后成功下载，但 gcc-c++（13 MB）连续两次 HTTP/2 流中断后耗尽所有镜像重试机会，导致 `dnf install` 整体失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 GrADS Dockerfile（含正常的 `dnf install` 依赖安装步骤），以及 README.md / image-info.yml / meta.yml 的条目补充。失败完全由构建时 openEuler 镜像仓库的 HTTP/2 网络传输异常引起，属于 CI 基础设施侧的瞬时问题。PR 代码本身没有错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是一个瞬时基础设施问题，重新触发 CI 构建（retry）即可。HTTP/2 流中断通常由仓库服务器负载波动或网络链路瞬时故障导致，重试大概率通过。

### 方向 2（置信度: 低）
如果同一 Dockerfile 反复遭遇此类 HTTP/2 错误，可在 Dockerfile 的 `dnf install` 命令中添加重试参数（如 `--setopt=retries=10`）或配置镜像源冗余，以提升对瞬时网络波动的容忍度。但当前日志显示仅一次构建失败，不建议为此增加不必要的复杂度。

## 需要进一步确认的点
- 确认该 openEuler 24.03-LTS-SP4 仓库在 CI 构建时间段内是否存在已知的服务端问题。
- 确认同一时间段内其他使用 openEuler 24.03-lts-sp4 基础镜像的 Dockerfile 构建（如本 PR 触发前/后的其他 job）是否也出现类似 HTTP/2 错误，以区分"仓库全局异常"还是"单次网络抖动"。

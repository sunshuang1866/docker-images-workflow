# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install, repo.***.org

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.***.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.***.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）。其中 cmake-data 和 git-core 经镜像重试后下载成功，但 gcc-c++ 两次重试均失败，最终「无更多可用镜像」导致整个 dnf install 步骤报错退出，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及其配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install` 的包列表语法正确、包名合理。失败根源是 openEuler 24.03-LTS-SP4 软件仓库在构建时段的 HTTP/2 传输不稳定，属于基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败是 openEuler SP4 仓库镜像的瞬时 HTTP/2 流错误所致，与 PR 代码无关。在其他时段重新触发 CI 构建，大概率可以成功完成 dnf 包下载。

### 方向 2（置信度: 低）
**添加 dnf 重试参数。** 在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=5 --setopt=timeout=120`，增强 dnf 对瞬时网络故障的容忍度。但这只是加固措施，不是根因修复——如果上游仓库持续不稳定，仍可能失败。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.***.org`）在该时段是否存在已知的 CDN/镜像稳定性问题。
- 观察同类 openEuler SP4 镜像的 CI 构建是否同期出现类似 Curl error (92) 失败，以排除是否为本 PR 的新 Dockerfile 触发了特殊的包组合下载。

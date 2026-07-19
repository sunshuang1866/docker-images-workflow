# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在下载 `gcc-c++` RPM 包时反复出现 HTTP/2 framing 层流错误（Curl error 92），累计两次失败后 dnf 耗尽所有镜像重试次数，安装步骤以 exit code 1 终止。日志中另有 `cmake-data` 和 `git-core` 两个包也触发了相同 Curl error (92)，但它们在重试后成功下载，仅 `gcc-c++` 最终失败。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 的变更仅限于：
1. 新增 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）——dns install 命令语法正确，包名列表与同类 sp3 版本一致
2. 更新 `README.md`、`doc/image-info.yml`、`meta.yml` 中的版本条目

失败发生在 Docker 构建层 `#7 [2/3] RUN dnf install -y ...`，是 openEuler 24.03-LTS-SP4 官方仓库镜像的 HTTP/2 传输层间歇性故障。258 个待安装包中绝大多数下载成功，仅 `gcc-c++`（13 MB）在两次重试后仍因 HTTP/2 stream INTERNAL_ERROR 无法完成下载。Dockerfile 本身无需修改。

## 修复方向

### 方向 1（置信度: 高）
**等待仓库恢复后重试。** 这是 CI 基础设施问题（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 服务不稳定），PR 代码变更无任何错误。建议在仓库镜像网络恢复后重新触发 CI 构建（`retest` 或 `recheck`），无需修改任何文件。

### 方向 2（置信度: 低）
**如果问题持续复现**，可在 Dockerfile 的 `dnf install` 命令前增加 `RUN echo 'retries=10' >> /etc/dnf/dnf.conf && echo 'timeout=120' >> /etc/dnf/dnf.conf` 提高 dnf 下载容错能力。但这只是缓解措施，根本问题仍在于仓库侧 HTTP/2 传输稳定性。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在当前时间段是否存在 HTTP/2 服务异常或 CDN 节点故障
2. 确认其他同样使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也在同一时间段遭遇相同的 Curl error (92)

## 修复验证要求
无需修复验证——此为 infra-error，不涉及代码修改。直接重新触发 CI 构建即可验证。

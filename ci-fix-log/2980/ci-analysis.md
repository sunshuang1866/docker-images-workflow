# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像在上层 HTTP/2 传输层出现间歇性连接错误（Curl error 92 / INTERNAL_ERROR），导致 `cmake-data`、`git-core`、`gcc-c++` 三个 RPM 包的下载流被异常中断。前两者在重试后成功，但 `gcc-c++`（约 13MB）两次尝试均失败，最终 dnf 耗尽所有镜像后报错退出。

### 与 PR 变更的关联
本次失败与 PR 代码变更**无直接关系**。PR 新增的 Dockerfile 内容语法正确、依赖列表完整（参照已有 sp3 版本的同目录 Dockerfile 推断）。失败原因是 openEuler 24.03-LTS-SP4 的软件源镜像/网络在 CI 构建时刻出现 HTTP/2 协议层面的不稳定——这是一个基础设施问题，不影响 Dockerfile 的正确性。

## 修复方向

### 方向 1（置信度: 中）
**基础设施侧排查，无需修改代码。** 该错误为 CI 运行环境与 openEuler 24.03-LTS-SP4 软件源镜像之间的 HTTP/2 传输层问题（Curl error 92 / INTERNAL_ERROR）。可能的原因包括：
- 软件源镜像的 HTTP/2 实现存在 bug（特定包大小触发）
- CI runner 与镜像之间的代理/防火墙干扰了 HTTP/2 多路复用流
- 临时性网络波动

建议先触发一次**重新构建**（retry），验证是否为临时问题。若重试仍失败，需从基础设施层面排查 HTTP/2 兼容性（如强制 dnf 使用 HTTP/1.1，或将 `repo.****.org` 切换为其他可用镜像源）。

### 方向 2（置信度: 低）
若重试多次仍持续失败，可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=proxy=` 或配置 `ip_resolve=4` 绕过可能存在的 HTTP/2 代理问题。但这属于临时规避，不应作为长期方案。

## 需要进一步确认的点
1. 该 CI runner 是否通过代理访问外部软件源？代理是否支持 HTTP/2？
2. 失败的三个包（cmake-data、git-core、gcc-c++）是否有共性特征（如包大小超过某个阈值导致 HTTP/2 流中断）？
3. 同一时间段内、同一 CI runner 上其他使用 openEuler 24.03-LTS-SP4 基础镜像的构建是否也出现类似错误？（若需确认是否需要将镜像源切换至其他区域/协议）
4. 重新触发 CI 构建是否能通过？

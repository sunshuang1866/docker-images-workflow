# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, gcc-c++, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在通过 HTTP/2 协议传输 RPM 包时出现流帧层错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` 等关键 RPM 包下载失败，`dnf install` 命令退出码为 1。日志中同样出现了 `cmake-data` 和 `git-core` 的同类型 Curl error (92)，说明这是仓库端普遍性的 HTTP/2 协议问题，非偶发故障。

### 与 PR 变更的关联
**与 PR 变更无关。** 该失败是 CI 构建环境访问 openEuler 24.03-LTS-SP4 软件仓库时遭遇的网络/协议层基础设施问题。PR 仅新增了一个合法的 Dockerfile（语法正确，`dnf install` 包列表与同级 sp3 版本一致），以及对应的 README、image-info.yml、meta.yml 文档更新。即使 Dockerfile 不存在，该仓库的 HTTP/2 协议错误依然会发生。

## 修复方向

### 方向 1（置信度: 高）
**等待 CI 基础设施恢复 / 重试构建。** 该错误为 `repo.****.org` 仓库服务器的 HTTP/2 协议层故障，属于临时性基础设施问题。建议在仓库管理员确认 `repo.****.org` 服务恢复正常后，重新触发 CI 构建（retrigger）。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
如果该仓库节点持续不可用，可考虑在 Dockerfile 中添加 `--setopt=timeout=300 --retries=10` 等 dnf 重试参数以提高网络抗波动能力。但这类调整治标不治本，根源是服务端 HTTP/2 协议异常。

## 需要进一步确认的点
- 该 `repo.****.org` 仓库节点是否仅对特定架构（如 x86_64）的 HTTP/2 连接存在问题，还是所有请求均受影响——可尝试通过 `curl --http1.1` 降级到 HTTP/1.1 协议验证服务是否正常。
- 是否有备选镜像源（如同仓库的其他 mirror 节点）可以直接替换，绕过问题节点。

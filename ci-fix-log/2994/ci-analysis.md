# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器异常终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, EOF, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建阶段 Step #7（`dnf install` 正在下载 OS 仓库元数据时）
- 失败原因: BuildKit 构建器 `euler_builder_20260709_224657` 在构建进行中（dnf 安装系统依赖包）收到 `graceful_stop` 信号后被终止，gRPC 连接随之中断（EOF），随后构建器实例被销毁（"no builder found"）。这是 CI 基础设施层面的问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 变更仅为新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（标准 Dockerfile，安装 gcc/make/python 等基础构建工具后 pip 安装 scann）及配套的 README、image-info.yml、meta.yml 更新。构建在 `dnf install` 阶段就因 BuildKit builder 被终止而中止，尚未执行到 `pip install scann` 等 PR 特有步骤。Dockerfile 本身语法和内容无错误——基础镜像 `openeuler/openeuler:24.03-lts-sp4` 已成功拉取（Step #6 DONE），Step #7 的 `dnf install` 命令也是标准的系统包安装操作。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。BuildKit 构建器的 `graceful_stop` 和 "no builder found" 是 CI 基础设施的瞬时故障（如构建节点资源回收、BuildKit daemon 重启、构建超时被 kill 等），与 PR 代码无关。重新触发一次 CI pipeline 大概率能正常通过。

### 方向 2（置信度: 低）
若重试后仍失败，检查 CI 构建节点的资源限制（内存/磁盘），确认 `dnf install` 大量包时是否因 OOM 或磁盘空间不足导致 builder 被终止。

## 需要进一步确认的点
- 若重试后仍失败，需获取 CI 构建节点的系统日志（dmesg/syslog）检查是否有 OOM killer 记录或磁盘空间告警。
- 确认 BuildKit daemon 版本及该构建节点上是否存在频繁的 daemon 重启日志。

## 修复验证要求
（无需验证——修复方向仅为重新触发 CI，不涉及代码或正则修改。）

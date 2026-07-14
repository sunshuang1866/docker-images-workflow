# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: BuildKit构建器被终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, buildkit

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker build 步骤 `#7 [2/4] RUN dnf install -y ...`
- 失败原因: BuildKit 构建器实例 `euler_builder_20260709_224657` 在执行 `dnf install` 期间被终止。日志显示 `dnf` 正在下载仓库元数据（速度仅 77 kB/s，下载 2.8 MB 耗时约 37 秒），此时 BuildKit 守护进程发送了 `graceful_stop` 信号并关闭连接，导致构建中断。最终构建器被移除（`no builder found`）。

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增了 scann 1.4.2 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法正确、包名有效。失败原因是在 `dnf install` 下载仓库元数据阶段（尚未进入包安装阶段），BuildKit 构建器被基础设施层面终止。PR 的代码变更不会触发此类 Builder 生命周期管理问题。

## 修复方向

### 方向 1（置信度: 中）
**CI 基础设施重试**。该失败为 BuildKit 构建器因超时或资源回收被终止导致的瞬时基础设施问题，与 PR 代码无关。建议 re-trigger CI 构建（在 Jenkins 中点击 "重试" 或重新 push 触发），大概率可通过。

### 方向 2（置信度: 低）
**dnf 镜像源慢导致超时**。日志中 dnf 元数据下载速度仅 77 kB/s，若 CI 为 BuildKit builder 设置了超时阈值，极慢的网络可能导致 builder 在元数据下载完成前被回收。若重试持续失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 或更换更快的 yum 镜像源（如华为云 `repo.huaweicloud.com`）。

## 需要进一步确认的点
1. 确认 CI 环境中 BuildKit builder 的超时配置是多少（日志显示 `dnf` 元数据下载耗时约 37 秒，若超时设为 30-40 秒则刚好触发）
2. 确认 `euler_builder_20260709_224657` 被终止的原因——是 OOM、超时回收还是 Jenkins 节点清理策略
3. 确认重试后是否稳定通过；若多次复现，可能需要调查 CI 节点到 openEuler 仓库的网络质量

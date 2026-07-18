# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器意外终止
- 新模式症状关键词: graceful_stop, no builder found, closing transport, connection error, EOF

## 根因分析

### 直接错误
```
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: BuildKit docker-container builder 实例 `euler_builder_20260709_224657`
- 失败原因: BuildKit 构建器在 Docker 构建执行到步骤 `#7 [2/4] RUN dnf install -y gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel && dnf clean all`（正在下载仓库元数据，已运行约 39 秒）时被意外终止。goaway 原因为 `graceful_stop`（NO_ERROR），表明构建器守护进程被有意停止（可能是 CI runner 回收、节点维护或 builder 超时），并非构建代码本身出错。

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增了 4 个文件：
- 新增 Dockerfile `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile`（语法和逻辑均正确）
- 更新 `Others/scann/README.md`、`Others/scann/doc/image-info.yml`、`Others/scann/meta.yml`（均为元数据补充）

Docker 构建本身尚未到达 PR 代码可能引发问题的阶段（dnf install 是基础依赖安装，在所有 Dockerfile 中通用且已验证），构建器在下载 openEuler 仓库元数据时被基础设施层面终止。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 BuildKit builder 基础设施的一次性故障（构建器被 `graceful_stop` 终止），与 PR 代码变更无关。通常重新运行失败 job 即可通过。

### 方向 2（置信度: 低）
如果重试后仍反复出现 builder 在相同步骤（`dnf install`）被终止的问题，可能是 builder 实例的资源配额不足（内存/OOM）或 builder 空闲超时配置过短。但当前日志中无 OOM kill 或显式超时信息，此方向仅为推测。

## 需要进一步确认的点
- 本次失败是否为该 PR 的首次构建尝试（若为首次，重试基本可确认是偶发 infra 故障）
- 构建器 `euler_builder_20260709_224657` 被 `graceful_stop` 的具体原因（CI 平台侧日志可能有更多信息，如节点回收计划、维护窗口等）

## 修复验证要求
无需验证 —— 此失败为 infra-error，不涉及代码修改。

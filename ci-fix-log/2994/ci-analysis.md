# CI 失败分析报告

## 基本信息
- PR: #2994 — chore(scann): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 构建器意外终止
- 新模式症状关键词: `failed to receive status`, `rpc error`, `Unavailable`, `closing transport`, `error reading from server: EOF`, `graceful_stop`, `no builder`

## 根因分析

### 直接错误
```
#7 [2/4] RUN dnf install -y       gcc gcc-c++ make wget       openssl-devel bzip2-devel zlib-devel &&     dnf clean all
#7 38.59 OS                                               77 kB/s | 2.8 MB     00:37    
ERROR: failed to receive status: rpc error: code = Unavailable desc = closing transport due to: connection error: desc = "error reading from server: EOF", received prior goaway: code: NO_ERROR, debug data: "graceful_stop"
ERROR: no builder "euler_builder_20260709_224657" found
```

### 根因定位
- 失败位置: Docker 构建步骤 #7（`dnf install` 阶段），日志未指示 Dockerfile 内代码行号错误
- 失败原因: CI 的 BuildKit 构建器实例 `euler_builder_20260709_224657` 在构建中途被**外部原因**强制优雅关闭（gRPC GOAWAY 信号 + graceful_stop 调试数据），与 PR 的 Dockerfile 内容无关

## 与 PR 变更的关联

该失败**与 PR 变更无关**。PR 仅新增了一个标准的 Dockerfile（安装编译依赖 → 编译 Python 3.9.19 → pip 安装 scann）和配套元数据文件，所有变更在语法和逻辑上均无错误。

具体分析如下：

1. **构建卡在 dnf 元数据下载阶段**：step #7 正在从 openEuler 仓库拉取 2.8 MB 的 yum/dnf 元数据，耗时约 38 秒（速度 77 kB/s），尚未进入实际包安装环节，Dockerfile 中指定的包列表（`gcc`, `gcc-c++`, `make`, `wget`, `openssl-devel`, `bzip2-devel`, `zlib-devel`）尚未被解析和校验。
2. **错误来自 BuildKit 基础设施层**：`graceful_stop` 是 BuildKit server 发出的 HTTP/2 GOAWAY 信号，表示构建器实例被外部系统（如 CI 资源调度器、节点回收脚本、容器编排超时）主动终止，并非由 Docker 构建进程内部错误触发。
3. **"no builder found" 是级联错误**：因构建器实例已不存在，后续任何构建操作自然无法找到该 builder。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是 CI 基础设施的偶发性故障，BuildKit 构建器实例被意外终止。直接重新触发 CI workflow（retry）即可，无需修改任何代码。

## 需要进一步确认的点

1. CI 平台侧该 runner（`ecs-build-docker-x86-hk` / `docker-build-x86-01`）在对应时间段是否存在节点回收、资源超限或维护操作记录。
2. BuildKit 构建器实例 `euler_builder_20260709_224657` 的终止原因（容器 OOM、宿主机调度驱逐、CI job 超时等）需从 CI 平台基础设施日志中确认——但与本 PR 代码无关。
3. **额外注意（非本次失败原因）**：Dockerfile 中 pip 安装使用了镜像地址参数 `-i https://pypi.tuna.tsinghua.edu.cn/sync`，路径 `/sync` 与清华 PyPI 镜像的标准路径 `/simple` 不一致。当前构建未到达该步骤故而未被触发，但若此路径为笔误，后续构建在通过 dnf 阶段后可能因该 URL 不可达而失败。建议在 CI 重试成功后确认该 pip 命令是否执行正常。

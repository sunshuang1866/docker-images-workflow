# CI 失败分析报告

## 基本信息
- PR: #2759 — 【自动升级】logstash容器镜像升级至9.4.2版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式06
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#15 [11/13] COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml
#15 ERROR: failed to calculate checksum of ref fbx39111od3h1pv8s8xdtage8::zk811rb2fuyobxitk8n2bttt8: "/env2yaml/env2yaml-amd64": not found
------
 > [11/13] COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml:
------
ERROR: failed to solve: failed to compute cache key: failed to calculate checksum of ref fbx39111od3h1pv8s8xdtage8::zk811rb2fuyobxitk8n2bttt8: "/env2yaml/env2yaml-amd64": not found
```

### 根因定位
- 失败位置: `Bigdata/logstash/9.4.2/24.03-lts-sp3/Dockerfile:39`
- 失败原因: Dockerfile 中 `COPY env2yaml/env2yaml-${TARGETARCH} /usr/local/bin/env2yaml` 引用了 `env2yaml/env2yaml-amd64` 二进制文件，但该文件未随 Dockerfile 一起提交到仓库（build context 中 `env2yaml/` 目录下仅有 `.DS_Store`，缺少 `env2yaml-amd64` 和 `env2yaml-arm64` 两个架构的二进制文件）。

### 与 PR 变更的关联
本次 PR 新增了 logstash 9.4.2 的完整 Dockerfile 及配套配置文件，其中 Dockerfile 第 39 行引用了 `env2yaml/env2yaml-${TARGETARCH}` 二进制文件。从 PR diff 可见，`env2yaml/` 目录下仅提交了 `.DS_Store`（macOS 系统文件），而实际需要的架构二进制文件 `env2yaml-amd64` 和 `env2yaml-arm64` 未被包含在提交中。此问题与同一镜像的历史版本（9.4.0、9.3.4、9.3.3）完全一致，属于模式06的典型重现。

## 修复方向

### 方向 1（置信度: 高）
在 `Bigdata/logstash/9.4.2/24.03-lts-sp3/env2yaml/` 目录下补充提交 `env2yaml-amd64` 和 `env2yaml-arm64` 两个架构的二进制文件（可从 logstash 9.4.0 的同名目录复制，或从上游 Elastic 镜像中提取对应架构的 `env2yaml` 工具）。

## 需要进一步确认的点
- 确认 `env2yaml-amd64` 和 `env2yaml-arm64` 二进制是否与 logstash 9.4.2 版本兼容（可直接复用 9.4.0 版本的二进制，或从 logstash 9.4.2 官方镜像中提取）。
- 确认 `env2yaml/` 目录下的 `.DS_Store` 文件是否需要一并清理（macOS 系统文件，非项目所需）。

# 修复摘要

## 修复的问题
Dockerfile 中 `COPY env2yaml/env2yaml-${TARGETARCH}` 引用的 `env2yaml-amd64` / `env2yaml-arm64` 二进制文件缺失，导致 Docker 构建失败。

## 修改的文件
- `Bigdata/logstash/9.4.2/24.03-lts-sp3/Dockerfile`: 改为多阶段构建，从官方 Elastic logstash 9.4.2 镜像中复制 `env2yaml` 工具（shell 脚本 + Java classes/lib），替代原来依赖缺失的本地预编译二进制文件。

## 修复逻辑
提交缺失的二进制文件（`env2yaml-amd64` / `env2yaml-arm64`）不在 `pr.changed_files` 列表内且禁止新增文件，因此改为修改 Dockerfile 本身。通过多阶段构建 `FROM docker.elastic.co/logstash/logstash:9.4.2 AS env2yaml-src` 并从该镜像 COPY `env2yaml` shell 脚本及配套的 `classes/` 和 `lib/` 目录到目标镜像，消除了对缺失本地二进制文件的依赖。`env2yaml` 的 shell 脚本入口兼容 `entrypoint.sh` 的调用方式（`env2yaml /usr/share/logstash/config/logstash.yml`），使用的 JVM 来自已下载的 logstash 发行版。

CI 分析报告中根因是：`env2yaml/` 目录下仅提交了 `.DS_Store`，缺少 `env2yaml-amd64` 和 `env2yaml-arm64` 两个架构二进制文件。

## 潜在风险
- 修复引入了对 `docker.elastic.co/logstash/logstash:9.4.2` 镜像的网络依赖，若该镜像不可达则构建仍会失败。但 Dockerfile 中已有 `curl` 到 `artifacts.elastic.co` 的网络请求，说明构建环境可访问 Elastic 网络资源。
- `env2yaml` 从原生二进制改为 JVM shell 脚本实现，启动时有轻微 JVM 冷启动开销（约数十毫秒），不影响功能正确性。
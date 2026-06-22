# CI 失败分析报告

## 基本信息
- PR: #2698 — Feat: add percona 8.4.8 docker image on openEuler 24.03-LTS-SP3
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式05
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#8 418.4 /bin/sh: line 1: groupadd: command not found
#8 ERROR: process "/bin/sh -c dnf install -y gcc gcc-c++ make cmake bison ncurses-devel openssl-devel ... && groupadd -r mysql && useradd -r -g mysql mysql && ..." did not complete successfully: exit code: 127
------
Dockerfile:9
--------------------
   9 | >>> RUN dnf install -y gcc gcc-c++ make cmake bison ncurses-devel openssl-devel \
  10 | >>>         libtirpc-devel rpcgen m4 wget libcurl-devel && \
  11 | >>>     groupadd -r mysql && useradd -r -g mysql mysql && \
```

### 根因定位
- 失败位置: `Cloud/percona/8.4.8/24.03-lts-sp3/Dockerfile:11`
- 失败原因: `openeuler:24.03-lts-sp3` 基础镜像默认不包含 `shadow-utils` 包，导致 `groupadd` 和 `useradd` 命令不存在（exit code 127）。

### 与 PR 变更的关联
PR 新增了整个 percona Dockerfile，其中第 9-11 行的 `RUN` 指令在 `dnf install` 完成后立即执行 `groupadd -r mysql && useradd -r -g mysql mysql`。该 PR 的 `dnf install` 列表遗漏了 `shadow` 包（openEuler 中提供 `groupadd`/`useradd` 的包名），直接触发了此失败。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 第 9 行的 `dnf install` 命令中添加 `shadow` 包，使 `groupadd` 和 `useradd` 命令在基础镜像中可用。这是 openEuler 平台上 `shadow-utils` 的包名，与历史模式05的修复方式一致。

## 需要进一步确认的点
- 确认 aarch64 架构构建 job 是否也因同一原因失败（日志中仅有 x86-64 构建信息）。
- 确认 openEuler 24.03-LTS-SP3 仓库中 `shadow` 包名未变更（当前已知包名为 `shadow`，对应标准发行版的 `shadow-utils`）。

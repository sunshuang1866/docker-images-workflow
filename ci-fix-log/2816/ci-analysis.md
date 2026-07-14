# CI 失败分析报告

## 基本信息
- PR: #2816 — chore(daos): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: GitHub Raw 限流 (HTTP 429)
- 新模式症状关键词: curl: (22), 429, raw.githubusercontent.com, BuildFailure, scons, mercury, na_ucx.patch

## 根因分析

### 直接错误
```
#11 52.40 Downloading source for mercury
#11 52.40 RUN: curl -sSfL --retry 10 --retry-max-time 60 -o /daos/build/external/release/mercury_... https://raw.githubusercontent.com/daos-stack/mercury/f3dc286fb40ec1a3a38a2e17c45497bc2aa6290d/na_ucx.patch
#11 56.66 curl: (22) The requested URL returned error: 429
#11 60.90 curl: (22) The requested URL returned error: 429
#11 66.13 curl: (22) The requested URL returned error: 429
#11 73.77 curl: (22) The requested URL returned error: 429
#11 85.02 curl: (22) The requested URL returned error: 429
#11 104.3 curl: (22) The requested URL returned error: 429
#11 139.5 curl: (22) The requested URL returned error: 429
#11 139.5 BuildFailure: https://raw.githubusercontent.com/daos-stack/mercury/f3dc286fb40ec1a3a38a2e17c45497bc2aa6290d/na_ucx.patch failed to build:
#11 139.5   File "/daos/site_scons/prereq_tools/base.py", line 1022:
#11 139.5     raise BuildFailure(raw)
```

### 根因定位
- 失败位置: DAOS scons 构建阶段，mercury 依赖的 patch 下载步骤（`/daos/site_scons/prereq_tools/base.py:1022`）
- 失败原因: CI runner 从 `raw.githubusercontent.com` 下载 mercury 的 `na_ucx.patch` 时，GitHub 返回 HTTP 429（Too Many Requests），curl 在 `--retry 10 --retry-max-time 60` 范围内全部重试均失败（从 `#11 56.66` 到 `#11 139.5`，约 87 秒内全部返回 429），scons 构建系统在补丁下载环节抛出 `BuildFailure` 异常。`raw.githubusercontent.com` 对未认证请求有严格的 IP 级别速率限制（约 60 次/小时），CI 环境可能因并发构建多个项目而导致触发该限制。

### 与 PR 变更的关联
PR 新增了一个 DAOS 2.6.3 on openEuler 24.03-LTS-SP4 的 Dockerfile，该 Dockerfile 在构建时执行 `scons --build-deps=yes install`，其中 mercury 依赖的构建需要从 GitHub Raw 下载补丁文件。PR 的代码变更本身没有错误，但由于 DAOS 的构建依赖链需要在 CI 环境中实时下载外部补丁，该 CI runner 的出口 IP 可能已被 GitHub 限流，导致下载失败。**此失败与 PR 代码变更无直接因果关系，属于 CI 基础设施层面的网络问题。**

此外，日志中还暴露了两个 Dockerfile 自身的 UndefinedVar lint 警告（不构成构建失败，但需修正）：
```
- UndefinedVar: Usage of undefined variable '$CPATH' (did you mean $PATH?) (line 31)
- UndefinedVar: Usage of undefined variable '$daospath' (line 32)
```
- line 31: `ENV CPATH=/daos/install/include/:$CPATH` — `$CPATH` 自引用未定义变量，应设为 `${CPATH:-}`。
- line 32: `ENV PATH=/daos/install/bin/:${daospath}/install/sbin:$PATH` — `${daospath}` 变量从未定义，疑似应为 `${PATH}` 或 `/daos`。

## 修复方向

### 方向 1（置信度: 中）
将 mercury 的 `na_ucx.patch` 补丁文件预下载并嵌入 Docker 构建上下文，避免在 `scons` 构建阶段实时从 GitHub Raw 下载。具体做法：在 Dockerfile 中 `git clone daos` 之后、`scons` 之前，先用 `git clone` 或 `wget` 提前将补丁文件下载到 scons 期望的路径（即 `/daos/build/external/release/mercury_*_na_ucx.patch_1`），或通过 `COPY` 将预置的补丁文件放入容器。

### 方向 2（置信度: 低）
在 CI runner 上配置 GitHub token 认证（如 `GITHUB_TOKEN` 环境变量或 `.netrc`），使 `raw.githubusercontent.com` 的请求携带认证信息，从而免除未认证请求的速率限制。此方向需要改动 CI pipeline 配置，超出 Dockerfile 范畴。

## 需要进一步确认的点
1. **是否为 CI 环境的持续问题**：需要确认同一 CI runner 近期其他 PR 的构建是否也出现了 GitHub Raw 429 限流错误。如果是持续性问题，可能需要运维层面解决（如为 CI runner 出口 IP 配置 GitHub token、或设置本地 HTTP 代理缓存）。
2. **补丁文件内容**：需要从 `https://raw.githubusercontent.com/daos-stack/mercury/f3dc286fb40ec1a3a38a2e17c45497bc2aa6290d/na_ucx.patch` 获取该补丁的实际内容，确认将其嵌入构建上下文是否可行（大小、格式等）。
3. **其他 daos 版本的构建是否受影响**：同仓库中 `Storage/daos/2.6.3/24.03-lts-sp2/Dockerfile` 的 CI 构建是否也因同样原因失败，还是仅 SP4 环境触发此问题。
4. **Dockerfile UndefinedVar 修正**：确认 `line 32` 中 `${daospath}` 的预期值（应为 `/daos` 还是其他路径），一并修正 line 31 的 `$CPATH` 自引用问题。

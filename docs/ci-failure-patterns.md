# CI 失败模式知识库

> **按失败模式分类**，每个模式包含：典型报错、根因分析、修复方法、历史案例。  
> 处理新失败 PR 时，**用报错关键词搜索对应章节**，直接找到修复方法。

---

## 模式01：Apache CDN Maven 版本 404

**症状关键词**: `dlcdn.apache.org` `404 Not Found` `maven`

**根因**: `dlcdn.apache.org` 只托管当前最新版 Maven，旧版本下架后返回 404。

**典型报错**:
```
> [3/7] RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.14/binaries/apache-maven-3.9.14-bin.tar.gz
0.110 --2026-05-11 02:46:31--  https://dlcdn.apache.org/maven/maven-3/3.9.14/binaries/...
404 Not Found
0.297 2026-05-11 02:46:31 ERROR 404: Not Found.
------
Dockerfile:12
```

**修复方法**（两种，按情况选择）:
1. **换镜像站**：将下载源改为 `repo.huaweicloud.com/apache/maven/maven-3/` 或 `archive.apache.org/dist/maven/`，保留历史版本
2. **升级版本**：将 `MAVEN_VERSION` 升为 Apache CDN 当前可用版本（如 3.9.14、3.9.12）

**历史案例**:
- PR #2265: `Others/netty/4.2.13` — Maven 3.9.14 在 CDN 404 → 换华为云镜像站
- PR #2100: `Others/netty/4.2.12` — Maven 3.9.12 在 CDN 404 → 升级到 3.9.14
- PR #1884: `Others/netty/4.2.10` — Maven 3.9.11 在 CDN 404 → 升级到 3.9.12，文件名改用变量

---

## 模式02：下载 URL 硬编码版本路径错误 / 软件包版本不存在

**症状关键词**: `404 Not Found` `wget` `does not exist`

**根因**: URL 中版本目录路径硬编码（如目录写 `3.2` 但下载 `3.3.0`），或上游已停止对该平台版本提供制品。

**典型报错**:
```
> [4/6] RUN wget https://www.haproxy.org/download/3.2/src/haproxy-3.3.0.tar.gz
0.069 --2026-05-11 01:59:16--  https://www.haproxy.org/download/3.2/src/haproxy-3.3.0.tar.gz
404 Not Found
1.240 2026-05-11 01:59:17 ERROR 404: Not Found.
```

**修复方法**:
1. **动态生成 URL**：从 `VERSION` 变量中提取主次版本号（如 `${VERSION%.*}`）构造正确路径，替代硬编码
2. **换归档源 + 修正组合**：Phoenix 类问题需同时换用 `archive.apache.org/dist` 并修正平台标识（如 hbase-2.4 → hbase-2.5）

**历史案例**:
- PR #2267: `Others/haproxy/3.3.0` — URL 目录写 `3.2`，应为动态生成
- PR #1932: `Database/phoenix/5.3.0` — `phoenix-hbase-2.4-5.3.0-bin.tar.gz` 不存在（Phoenix 5.3.0 已弃 HBase 2.4） → 换 `archive.apache.org` + `hbase-2.5`

---

## 模式03：JDK / 二进制包版本在镜像站不存在（404）

**症状关键词**: `Adoptium` `OpenJDK` `404 Not Found` `mirrors.tuna`

**根因**: Dockerfile 中硬编码了 JDK 的具体 build 号（如 `11.0.28_6`），但镜像站只保留当前 build，旧 build 被覆盖后 404。

**典型报错**:
```
#10 0.087 --2026-04-06 01:14:48--  https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/x64/linux/OpenJDK11U-jre_x64_linux_hotspot_11.0.28_6.tar.gz
#10 0.317 Connecting to mirrors.tuna.tsinghua.edu.cn|101.6.15.130|:443... connected.
#10 0.503 HTTP request sent, awaiting response... 404 Not Found
```

**修复方法**: 将 JDK 版本升级为 Adoptium/镜像站当前实际可用的 build（查询镜像站目录确认版本号后再提交）。

**历史案例**:
- PR #2105: `Bigdata/kyuubi/1.11.1` — JDK 11.0.28_6 404 → 升级到 11.0.30_7

---

## 模式04：镜像站 403（访问被拒）

**症状关键词**: `403 Forbidden` `mirrors.ustc.edu.cn`

**根因**: 部分镜像站（如 USTC）对 CI 构建环境的请求触发防爬限制，返回 403。

**典型报错**:
```
wget https://mirrors.ustc.edu.cn/gnu/gcc/gcc-15.2.0/gcc-15.2.0.tar.gz
--2026-04-24 14:21:05--  https://mirrors.ustc.edu.cn/gnu/gcc/gcc-15.2.0/gcc-15.2.0.tar.gz
Connecting to mirrors.ustc.edu.cn|202.141.160.110|:443... connected.
HTTP request sent, awaiting response... 403 Forbidden
2026-04-24 14:21:06 ERROR 403: Forbidden.
```

**修复方法**: 将下载源从 `mirrors.ustc.edu.cn` 替换为 `mirrors.tuna.tsinghua.edu.cn`（清华镜像站对 CI 环境兼容性更好）。

**历史案例**:
- PR #2212: `Others/gcc/16.1.0` — USTC 403 → 清华镜像站

---

## 模式05：groupadd / useradd: command not found（缺 shadow-utils）

**症状关键词**: `groupadd: command not found` `useradd: command not found`

**根因**: `openeuler:24.03-lts-sp3` 基础镜像默认**不包含** `shadow-utils`，导致 `groupadd`/`useradd` 命令不存在。

**典型报错**:
```
49.71 /bin/sh: line 1: groupadd: command not found
```

**修复方法**: 在 Dockerfile 的第一个 `dnf install` 步骤中添加 `shadow` 包（openEuler 中 shadow-utils 的包名为 `shadow`）。

```dockerfile
RUN dnf install -y shadow python3-pip ...
```

**历史案例**:
- PR #2266: `AI/mlflow/3.12.0`
- PR #2164: `AI/mlflow/3.11.1`
- PR #1858: `AI/mlflow/3.9.0` — 同类问题，两架构均失败

---

## 模式06：COPY 目标文件不存在（env2yaml 二进制未提交到仓库）

**症状关键词**: `failed to calculate checksum` `not found` `env2yaml`

**根因**: Dockerfile 中 `COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml` 引用的二进制文件**未随 Dockerfile 一起提交**到仓库。

**典型报错**:
```
#15 [11/13] COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml
#15 ERROR: failed to calculate checksum of ref kzw8fcgm9psa1a0kbi7cp9fx0::...: "/env2yaml/env2yaml-amd64": not found
```

**修复方法**: 在同一目录下补充提交 `env2yaml/env2yaml-amd64` 和 `env2yaml/env2yaml-arm64` 两个架构的二进制文件。

**历史案例**:
- PR #2264: `Bigdata/logstash/9.4.0`
- PR #2206: `Bigdata/logstash/9.3.4`
- PR #2163: `Bigdata/logstash/9.3.3`

---

## 模式07：Maven 版本不满足项目 enforcer 约束

**症状关键词**: `RequireMavenVersion` `is not in the allowed range` `maven-enforcer`

**根因**: 项目的 `maven-enforcer-plugin` 指定了最低 Maven 版本要求（如 `[3.9.11,)`），而 Dockerfile 中安装的 Maven 版本（如 3.9.1）低于该要求。

**典型报错**:
```
#8 69.10 [ERROR] Rule 5: org.apache.maven.enforcer.rules.version.RequireMavenVersion failed with message:
#8 69.10 [ERROR] Detected Maven Version: 3.9.1 is not in the allowed range [3.9.11,).
#8 69.10 [ERROR] -> [Help 1]
#8 ERROR: process "/bin/sh -c git clone -b ${VERSION} ... && mvn clean install ..." did not complete successfully: exit code: 1
```

**修复方法**: 将 Dockerfile 中的 Maven 版本从旧版（如 3.9.1）升级到满足约束的版本（如 3.9.14）。注意同时确认新版 Maven 在 `dlcdn.apache.org` 可用（否则参考模式01换源）。

**历史案例**:
- PR #2207: `Database/neo4j/2026.04.0` — 要求 >= 3.9.11，安装了 3.9.1 → 升级到 3.9.14
- PR #2102: `Database/neo4j/2026.03.1` — 同类问题 → 升级到 3.9.14

---

## 模式08：cmake patch hunk 应用失败（上游代码变更导致偏移量不匹配）

**症状关键词**: `Hunk #N FAILED` `patch unexpectedly ends` `.rej` `cmake_curl.patch`

**根因**: 补丁文件（如 `cmake_curl.patch`）是针对特定版本上游代码生成的，上游代码更新后行号偏移，导致 `patch` 命令 hunk 应用失败。

**典型报错**:
```
#13 0.064 patching file cmake/external.cmake
#13 0.064 Hunk #1 succeeded at 937 (offset 43 lines).
#13 0.064 patch unexpectedly ends in middle of line
#13 0.064 Hunk #2 FAILED at 1099.
#13 0.064 1 out of 2 hunks FAILED -- saving rejects to file cmake/external.cmake.rej
#13 ERROR: process "/bin/sh -c patch -Np1 < cmake_curl.patch && ./build.sh" did not complete successfully: exit code: 1
```

**修复方法**: 针对目标版本的实际上游源码**重新生成** patch 文件（`git diff` 生成），一并更新 Dockerfile 和 build.sh。

**历史案例**:
- PR #2209: `Database/tdengine/3.4.1.7` — cmake/external.cmake 行号偏移 43 行
- PR #2104: `Database/tdengine/3.4.1.1` — 同类问题

---

## 模式09：BuildKit 预定义变量 BUILDARCH 冲突

**症状关键词**: `BUILDARCH` `amd64` `404` `if [ "amd64" = "amd64" ]`

**根因**: `BUILDARCH` 是 BuildKit 的**预定义全局 ARG**（值为 `amd64`/`arm64`），在 `RUN` 中对其重新赋值（如 `BUILDARCH="x64"`）不会生效——BuildKit 会恢复为内置值，导致用错误架构字符串构造下载 URL，产生 404。

**典型报错**:
```
> [4/5] RUN if [ "amd64" = "amd64" ]; then BUILDARCH="x64"; ...
0.285 HTTP request sent, awaiting response... 404 Not Found
0.353 2026-05-04 00:12:49 ERROR 404: Not Found.
```

**修复方法**: 将变量名从 `BUILDARCH` 改为其他自定义名称（如 `MY_ARCH`、`JAVA_ARCH`），避免与 BuildKit 预定义变量冲突。

**历史案例**:
- PR #2211: `Others/spring-cloud/5.0.1`
- PR #2105: `Bigdata/kyuubi/1.11.1`（与 JDK 版本 404 叠加）

---

## 模式10：缺少构建依赖（CMake / configure 找不到系统库）

**症状关键词**: `Could NOT find` `cmake` `configure: error` `missing:` `-devel`

**根因**: Dockerfile 的 `dnf install` 步骤遗漏了编译所需的 `-devel` 库包，cmake/autoconf 配置阶段报错。

**典型报错（示例）**:
```
# libxml2 缺失
CMake Error: Could NOT find LibXml2 (missing: LIBXML2_LIBRARY LIBXML2_INCLUDE_DIR)

# PCRE 缺失
./configure: error: the HTTP rewrite module requires the PCRE library.

# protobuf-c 缺失
./configure: error: protoc-c not found. Please install protobuf-c-compiler package.

# MySQL Boost 缺失（表现为 CURL 报错，实为 Boost 未配置）
-- Could NOT find CURL (missing: CURL_LIBRARY CURL_INCLUDE_DIR)
```

**修复方法**: 根据报错的库名，在 `dnf install` 中补充对应的 `-devel` 包：

| 报错 | 需安装的包 |
|------|-----------|
| `LibXml2` not found | `libxml2-devel` |
| PCRE library required | `pcre pcre-devel` |
| `protoc-c` not found | `protobuf-c-compiler protobuf-c-devel` |
| MySQL Boost 未配置 | cmake 参数加 `-DDOWNLOAD_BOOST=1 -DWITH_BOOST=/tmp/boost` |

**历史案例**:
- PR #2210: `Others/wireshark/4.6.5` — 缺 `libxml2-devel`
- PR #2162: `Cloud/nginx/1.30.0` — 缺 `pcre pcre-devel`
- PR #1933: `Others/rsyslog/8.2602.0` — 缺 `protobuf-c-compiler protobuf-c-devel`
- PR #2205: `Database/mysql/9.7.0` — Boost 未配置，cmake 加 `-DDOWNLOAD_BOOST=1`

---

## 模式11：YAML / 元数据文件错误

**症状关键词**: `yaml.parser.ParserError` `expected '<document start>'` `version_suffix` `image-list.yml`

**根因**: 元数据文件（`meta.yml`、`image-info.yml`、`image-list.yml`）存在格式错误或字段名错误，导致 CI 预检阶段解析失败或一致性校验不通过。

**典型报错**:
```
yaml.parser.ParserError: expected '<document start>', but found '<block mapping start>'
  in "Others/fastjson/meta.yml", line 6, column 1
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

**修复方法**:

| 问题类型 | 修复操作 |
|---------|---------|
| YAML block mapping 格式错误 | 修正缩进或文档分隔符（`---`） |
| 字段名拼写错误 | 检查 CI schema，如 `version_suffix` → `version_prefix` |
| image-list.yml 条目遗漏 | 向对应的 `image-list.yml` 补充缺失的镜像条目 |
| 元数据包含不可用版本 | 从 `image-info.yml` 移除 beta/不稳定版本条目 |

**历史案例**:
- PR #2268: `Others/fastjson/meta.yml` — YAML 格式错误（block mapping start）
- PR #2270: `AI/diskann/doc/image-info.yml` — 字段名 `version_suffix` → `version_prefix`
- PR #2262: `Bigdata/image-list.yml` — 7 条镜像条目缺失
- PR #2269: `Database/milvus/doc/image-info.yml` — 包含不稳定 `3.0-beta` 版本条目
- PR #2512: `.claude/agents/README.md` — CI appstore 路径校验失败：`.claude/agents/README.md` 不在期望路径 `.claud
- PR #2512: `.claude/agents/README.md` — CI appstore 发布规范预检失败：`.claude/agents/README.md` 路径不符合预期，要求 R
- PR #2512: `.claude/README.md` — CI appstore 发布规范预检失败：`.claude/agents/README.md` 路径不符合规范，CI 期
- PR #2512: `.claude/README.md` — CI appstore 发布规范检查要求 `.claude/` 工具目录的 README 文件位于根层级 `.claud

---

## 模式12：上游代码目录结构变更（requirements / 配置路径迁移）

**症状关键词**: `No such file or directory` `requirements` `Could not open requirements file`

**根因**: 上游项目重组了目录结构，Dockerfile 中 `COPY` 或 `pip install -r` 引用的路径已失效。

**典型报错**:
```
#12 [build 1/2] RUN pip install -r requirements/cpu-build.txt
#12 0.668 ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements/cpu-build.txt'
#12 ERROR: process "/bin/sh -c pip install -r requirements/cpu-build.txt" did not complete successfully: exit code: 1
```

**修复方法**: 查看上游仓库对应版本的实际目录结构，更新 Dockerfile 中的路径引用。

**历史案例**:
- PR #2204: `AI/vllm-cpu/0.20.1` — requirements 从 `requirements/cpu-build.txt` 迁移到 `requirements/build/cpu.txt`

---

## 模式13：Shell 命令替换语法错误（$cmd 误写为命令）

**症状关键词**: `$nproc` `UndefinedVar` `make: *** Error 2`

**根因**: `nproc` 是 Shell 命令而非变量，`$nproc` 展开为空字符串，导致 make 使用默认并行数或产生语法错误。

**典型报错**:
```
make: *** [Makefile:156: all] Error 2
- UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 16)
```

**修复方法**: 将 `$nproc` 改为 `$(nproc)`（命令替换），或使用 `${NPROC:-$(nproc)}` 以支持外部覆盖。

**历史案例**:
- PR #2208: `Others/snort3/3.12.2.0` — `make -j $nproc` → `make -j $(nproc)`

---

## 模式14：pip 版本不兼容（pip 26.0 移除 API）

**症状关键词**: `AttributeError` `allow_all_prereleases` `PackageFinder` `pip`

**根因**: SPDK 等项目的 `pkgdep.sh` 在创建 Python venv 时使用 `--upgrade-deps` 将 pip 升级到 26.0，而 `pip-tools 7.5.2` 调用了 pip 26.0 中已删除的 `PackageFinder.allow_all_prereleases` 属性。

**典型报错**:
```
AttributeError: 'PackageFinder' object has no attribute 'allow_all_prereleases'
(x86_64 和 aarch64 的 check_build 均失败)
```

**修复方法**: 在 Dockerfile 中，运行 `pkgdep.sh` 前用 `sed` 删除脚本中的 `--upgrade-deps` 参数，使 venv 保留系统 pip 版本（与 pip-tools 兼容）：

```dockerfile
RUN sed -i 's/--upgrade-deps//g' scripts/pkgdep/rhel.sh && ./pkgdep.sh
```

**历史案例**:
- PR #1856: `Others/spdk/26.01` — pip-tools 7.5.2 与 pip 26.0 不兼容

---

## 模式15：编译错误——AVX512BF16 缺少 fallback 分支

**症状关键词**: `incomplete type` `qk_vec_type` `void` `AVX512BF16` `BFloat16`

**根因**: `KernelVecType<c10::BFloat16>` 只特化了 `__AVX512BF16__`/`__s390x__`/`__aarch64__` 三个分支，无 `#else`，导致在普通 x86_64（无 AVX512BF16 指令集支持）上 `qk_vec_type` 解析为 `void`，编译器报错。

**典型报错**:
```
error: incomplete type 'qk_vec_type' {aka 'void'} used in nested name specifier
```

**修复方法**: 在 Dockerfile 的 `git clone` 后，用 Python/sed patch 步骤应用 vllm-project/vllm PR #34052 的修复：将两个相同的 `#elif` 分支合并为单一 `#else`，使所有非 AVX512BF16 平台共用 `FP32Vec16` 计算路径。

**历史案例**:
- PR #1934: `AI/vllm-cpu/0.16.0`

---

## 模式16：RPM 包停止发布（换多阶段构建绕过）

**症状关键词**: `does not publish RPM` `RPM releases stopped` `404` RPM 下载

**根因**: 上游项目在某版本后停止了 RPM 包发布，CI 尝试下载时失败。

**修复方法**: 改用多阶段 Docker 构建，直接从官方 Docker 镜像中 `COPY` 二进制文件，替代从 RPM 安装：

```dockerfile
FROM grafana/agent:v0.44.7 AS agent-source
FROM openeuler/openeuler:24.03-lts-sp3
COPY --from=agent-source /bin/grafana-agent /usr/local/bin/grafana-agent
```

**历史案例**:
- PR #1857: `Cloud/grafana-agent/0.44.7` — v0.44.2 后无 RPM 发布

---

## 模式17：Copyright / SPDX 声明缺失

**症状关键词**: `check_package_license` `Copyright` `SPDX` `license check`

**根因**: 新增文件（Dockerfile、README.md、meta.yml、image-info.yml）未包含 Copyright 和 SPDX-License-Identifier 头，CI `check_package_license` 检查未通过。

**修复方法**: 为每类文件添加对应格式的版权头：

```dockerfile
# Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.
# SPDX-License-Identifier: MulanPSL-2.0
```

```markdown
<!-- Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved. -->
<!-- SPDX-License-Identifier: MulanPSL-2.0 -->
```

**历史案例**:
- PR #2516: `AI/vllm-cpu/0.22.1` — 4 个新增文件均缺少 Copyright + SPDX 头
- PR #2529: `Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile` — 为 PR #2529 涉及的 4 个文件补充缺失的 Copyright 和 SPDX-License-Identifie
- PR #2534: `Database/etcd/3.8.0-alpha.0/24.03-lts-sp3/Dockerfile` — 为4个缺失Copyright+SPDX声明的文件添加版权头，并修复Dockerfile中`make -j$nproc`的

---

## 模式18：git 浅克隆与 commit hash checkout 不兼容

**症状关键词**: `--depth 1` `git checkout` `commit hash` `2>/dev/null || true`

**根因**: `git clone --depth 1` 只拉取最新提交，历史 commit hash 不在浅克隆的可访问范围内；同时 `|| true` 静默掩盖了错误，导致 checkout 实际失败但构建继续，产生错误的构建结果。

**修复方法**: 将 checkout 逻辑从 `git checkout ${VERSION} 2>/dev/null || true` 改为先 `git fetch origin ${VERSION}` 再 `git checkout ${VERSION}`，或去掉 `--depth 1` 改为完整克隆。

**历史案例**:
- PR #2512: `Storage/3fs/22fca04` — `--depth 1` + commit hash checkout 不兼容
- PR #2526: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` — 修复 3FS Dockerfile 中 `git clone --recurse-submodules --shallo
- PR #2512: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` — `git clone --depth 1` 浅克隆后无法 checkout 指定 commit hash，导致 3FS 
- PR #2512: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24` — `git clone --depth 1` 浅克隆后无法 checkout 指定 commit hash `22fca0

---

## 模式19：证据不足 / 无法定位根因

适用于 CI 日志无法获取、PR 描述过于简略的情况，优先通过 diff 推断修复意图。

**历史案例**:
- PR #2489: `AI/diskann/0.52.0` — VERSION 变量引用方式有误（diff 推断）
- PR #2308: `AI/diskann/README.md` — 纯文档修正
- PR #1768: `Others/spring-cloud/5.0.0` — Dockerfile 重写，具体错误信息缺失
- PR #2537: `Database/milvus/3.0-beta/24.03-lts-sp3/Dockerfile` — 将4个文件的Copyright声明和SPDX-License-Identifier修改为openEuler社区规范格式（

---

## 模式20：x86-64构建日志缺失

**症状关键词**: missing build logs, downstream job, trigger-only, x86-64 only failure

**根因**: - 失败位置: **无法定位** — 下游 x86-64 构建 job（#1384）的日志未提供
- 失败原因: **证据不足，无法确定根因**

**修复方法**: 在 vllm-cpu 0.22.1 Dockerfile 中缺失 AVX512BF16 fallback patch，导致无 AVX512BF16 指令集的 x86_64 平台编译 `mla_decode.cpp` 时 `KernelVecType<c10::BFloat16>` 解析为 `void` 从而编译失败。

**历史案例**:
- PR #2527: `AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile` — 在 vllm-cpu 0.22.1 Dockerfile 中缺失 AVX512BF16 fallback patch，导

---

## 模式21：ENV自引用未定义变量

**症状关键词**: UndefinedVar, LD_LIBRARY_PATH, ENV

**根因**: - **失败位置**: `Others/libyuv/1948/24.03-lts-sp3/Dockerfile:19`
- **失败原因**: Dockerfile 中 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 在一个全新的构建阶段中自引用了 `$LD_LIBRARY_PATH`。由于该变量此前从未在同一构建阶段被定义，BuildKit 检测到对未定义变量的引用，产生 `UndefinedVar` 警告。

**修复方法**: Dockerfile 第 19 行 `ENV LD_LIBRARY_PATH` 自引用了未定义的 `$LD_LIBRARY_PATH` 变量，触发 BuildKit `UndefinedVar` 警告。

**历史案例**:
- PR #2546: `Others/libyuv/1948/24.03-lts-sp3/Dockerfile` — Dockerfile 第 19 行 `ENV LD_LIBRARY_PATH` 自引用了未定义的 `$LD_LIBRAR
- PR #2546: `Others/libyuv/1948/24.03-lts-sp3/Dockerfile` — Dockerfile 中 `ENV LD_LIBRARY_PATH` 自引用了未定义变量 `$LD_LIBRARY_PA

---

## 模式22：日志截断致证据不足

**症状关键词**: 日志截断, 未见致命报错, fbthrift, getdeps, boost SEND_ERROR

**根因**: - 失败位置: 无法定位 — 日志截断前未出现致命错误
- 失败原因: **证据不足，无法确定根因**。日志仅覆盖了 getdeps 依赖构建阶段（zstd → boost → glog → gflags → googletest），尚未进入 fbthrift 本身的编译。实际错误极可能发生在日志截断之后的阶段。

**修复方法**: 修复 `fix_getdeps.py` 中 `_verify_hash` 替换正则无法匹配「类中最后一个方法」的边界情况，导致 libaio tarball 哈希校验静默未被跳过。

**历史案例**:
- PR #2547: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py` — 修复 `fix_getdeps.py` 中 `_verify_hash` 替换正则无法匹配「类中最后一个方法」的边界情况
- PR #2547: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py` — 修复 `fix_getdeps.py` 中跳过 `_verify_hash` 方法替换的正则表达式边界缺陷：当 `_ve
- PR #2558: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py` — 修复 `fix_getdeps.py` 中 `_verify_hash` 方法匹配逻辑的 bug：原正则 `r'def 

---

## 模式23：RPM包名不存在

**症状关键词**: `Unable to find a match`, `No match for argument`, `boost-foundation`, `yum`, `开源组件RPM包名映射错误`

**根因**: - **失败位置**: 新增的 3FS Dockerfile（`Storage/3fs/<version>/<oe-version>/Dockerfile`）第 41 行
- **失败原因**: Dockerfile 的 `yum install` 命令中使用了 **openEuler RPM 仓库中不存在的包名**：
  - `boost-foundation` — openEuler 中无此 RPM 包名（可能是从其他发行版如 Ubuntu 的 `libboost-foundation-dev` 错误映射而来）
  - `boost-filesystem`、`boost-system`、`

**修复方法**: Dockerfile 中使用了 openEuler RPM 仓库中不存在的包名 `boost-foundation`，导致 `yum install` 失败；同时缺少 `libevent-devel` 致 CMake 配置阶段找不到 libevent。

**历史案例**:
- PR #2557: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` — Dockerfile 中使用了 openEuler RPM 仓库中不存在的包名 `boost-foundation`，导

---

## 模式24：NEON符号缺失链失败

**症状关键词**: undefined reference, RGBToUVMatrixRow_NEON, collect2: error, ld returned 1 exit status, aarch64

**根因**: - 失败位置: aarch64 架构构建（日志中安装的包均为 `.aarch64`），链接 `yuvconvert` 可执行文件时
- 失败原因: libyuv 1948 源码中，函数 `RGBToUVMatrixRow_NEON` 被 `convert.cc` 和 `row_any.cc` 调用，但其实现所在的源文件未被纳入 `yuv_common_objects` 或链接目标的编译/链接范围内，导致 aarch64 平台上产生未定义符号链接错误。日志显示 `yuv_neon64` 目标已成功编译（包含 `row_neon64.cc`、`rotate_neon64.cc`、`compare_

**修复方法**: libyuv 1948 在 aarch64 平台构建时，`RGBToUVMatrixRow_NEON` 函数实现缺失导致链接失败（undefined reference）。

**历史案例**:
- PR #2546: `Others/libyuv/1948/24.03-lts-sp3/Dockerfile` — libyuv 1948 在 aarch64 平台构建时，`RGBToUVMatrixRow_NEON` 函数实现缺失导致

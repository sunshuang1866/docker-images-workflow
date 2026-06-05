# CI 失败模式知识库

本文件由 ci-fix-team 自动维护，记录历史 CI 失败的根因与修复模式，供 AI 分析时参考。


---

## openeuler/openeuler-docker-images PR #2512 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定（证据不足）` |
| 置信度 | 低 |

**根因**:
- 失败位置: 无法定位（缺少子任务构建日志）
- 失败原因: 证据不足以确定根因。从上下文推断，失败最可能发生在以下环节之一：Dockerfile 的 RUN 命令执行过程中（编译错误、网络下载失败、命令语法错误），或是 CI 构建环境资源不足（超时、内存溢出）。

**修复方法**:
修复 Dockerfile 中浅克隆（`--depth 1`）与 `git checkout` 指定 commit hash 不兼容的构建逻辑缺陷。

**涉及文件**:
- `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`: 在第 23-24 行，将 `git checkout ${VERSION} 2>/dev/null || true` 替换为 `git fetch origin ${VERSION}` + `git checkout ${VERSION}`（移除错误静默掩盖）。


---

## openeuler/openeuler-docker-images PR #2516 · 2026-06-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `无法确定（证据不足）` |
| 置信度 | 低 |

**根因**:
- 失败位置: 无法定位（缺少 `x86-64 » openeuler-docker-images #1361` 的构建日志）
- 失败原因: 下游 x86-64 构建 job 失败，但其详细日志缺失，无法确定根因

**修复方法**:
为 CI `check_package_license` 检查未通过的 4 个新增文件添加 Copyright 声明头（缺失Copyright声明）。

**涉及文件**:
- `AI/vllm-cpu/0.22.1/24.03-lts-sp3/Dockerfile`: 添加 Copyright + SPDX 头
- `AI/vllm-cpu/README.md`: 添加 Copyright + SPDX 头（HTML注释格式）
- `AI/vllm-cpu/doc/image-info.yml`: 添加 Copyright + SPDX 头
- `AI/vllm-cpu/meta.yml`: 添加 Copyright + SPDX 头

---

## openeuler/openeuler-docker-images PR #2489 · 2026-06-02

| 字段 | 内容 |
|------|------|
| 失败类型 | `Dockerfile构建错误/变量引用错误` |
| 置信度 | 中 |

**根因**:
- 失败位置: `AI/diskann/0.52.0/24.03-lts-sp3/Dockerfile`
- 失败原因: Dockerfile 中 VERSION 变量的引用方式有误，导致构建时版本无法正确传递（推断为 `v${VERSION}` 前缀处理或 ARG/ENV 引用不一致）

**原始报错**（如能获取）:
```
无法获取日志，基于 diff 推断（+2/-5 行修改量）
```

**修复方法**:
修改 Dockerfile 中 VERSION 变量的引用方式（修正变量名引用或前缀处理逻辑），使构建时版本号能正确传递。

**涉及文件**:
- `AI/diskann/0.52.0/24.03-lts-sp3/Dockerfile`: 修正 VERSION 变量引用方式（+2/-5）

---

## openeuler/openeuler-docker-images PR #2308 · 2026-05-19

| 字段 | 内容 |
|------|------|
| 失败类型 | `文档更新（非CI构建失败）` |
| 置信度 | 中 |

**根因**:
- 失败位置: `AI/diskann/README.md`
- 失败原因: README 文档内容有误或过时，CI 的文档检查（如格式校验）可能未通过；也可能是纯文档勘误

**原始报错**（如能获取）:
```
无法获取日志，此 PR 为纯文档修正（+3/-3 行）
```

**修复方法**:
修正 `AI/diskann/README.md` 中的文档内容（3 处文本修改）。

**涉及文件**:
- `AI/diskann/README.md`: 文档内容修正（+3/-3）

---

## openeuler/openeuler-docker-images PR #2270 · 2026-05-18

| 字段 | 内容 |
|------|------|
| 失败类型 | `元数据YAML字段名错误` |
| 置信度 | 中 |

**根因**:
- 失败位置: `AI/diskann/doc/image-info.yml`
- 失败原因: CI 检查 image-info.yml 元数据格式时，字段名使用了 `version_suffix` 但应为 `version_prefix`，导致校验失败

**原始报错**（如能获取）:
```
无法获取日志，基于 PR 描述推断
```

**修复方法**:
将 `AI/diskann/doc/image-info.yml` 中的 `version_suffix` 字段名改为 `version_prefix`。

**涉及文件**:
- `AI/diskann/doc/image-info.yml`: 字段名 version_suffix → version_prefix（+1/-1）

---

## openeuler/openeuler-docker-images PR #2269 · 2026-05-16

| 字段 | 内容 |
|------|------|
| 失败类型 | `元数据版本列表包含不可用版本` |
| 置信度 | 中 |

**根因**:
- 失败位置: `Database/milvus/doc/image-info.yml`
- 失败原因: image-info.yml 中包含了 milvus 的 beta 版本（3.0-beta），CI 构建时该版本不可用或校验失败

**原始报错**（如能获取）:
```
无法获取日志，基于 PR 描述推断：Fix: add "beta" to version filter
```

**修复方法**:
从 `Database/milvus/doc/image-info.yml` 中移除 3.0-beta 版本条目，防止 CI 尝试构建不稳定的 beta 版本。

**涉及文件**:
- `Database/milvus/doc/image-info.yml`: 移除 3.0-beta 版本条目（+1/-1）

---

## openeuler/openeuler-docker-images PR #2268 · 2026-05-16

| 字段 | 内容 |
|------|------|
| 失败类型 | `YAML格式错误/元数据文件格式问题` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/fastjson/meta.yml` 的 CI 预检阶段
- 失败原因: meta.yml 文件存在 YAML 格式错误，导致 CI check_package_license 或构建预检解析失败

**原始报错**（如能获取）:
```
yaml.parser.ParserError: expected '<document start>', but found '<block mapping start>'
  in "Others/fastjson/meta.yml", line 6, column 1
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

**修复方法**:
修正 `Others/fastjson/meta.yml` 中的 YAML 格式错误（block mapping 缩进或分隔符问题），同时为 fastjson 2.0.62 提供正确格式的 Dockerfile。

**涉及文件**:
- `Others/fastjson/2.0.62/24.03-lts-sp3/Dockerfile`: 新增 fastjson 2.0.62 Dockerfile（修复 meta.yml 格式后重新提交）

---

## openeuler/openeuler-docker-images PR #2267 · 2026-05-16

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 404/版本路径硬编码错误` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/haproxy/3.3.0/24.03-lts-sp3/Dockerfile` RUN wget 步骤
- 失败原因: haproxy 下载 URL 中的版本目录路径硬编码为 `3.2`，但实际版本为 3.3.0，导致 404 Not Found

**原始报错**（如能获取）:
```
> [4/6] RUN wget https://www.haproxy.org/download/3.2/src/haproxy-3.3.0.tar.gz
0.069 --2026-05-11 01:59:16--  https://www.haproxy.org/download/3.2/src/haproxy-3.3.0.tar.gz
404 Not Found
1.240 2026-05-11 01:59:17 ERROR 404: Not Found.
```

**修复方法**:
使用环境变量动态构建下载 URL，从 VERSION 中提取主次版本号（如 `3.3`）构造正确路径，替代硬编码的 `3.2`。

**涉及文件**:
- `Others/haproxy/3.3.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，使用变量动态生成版本路径（+21）

---

## openeuler/openeuler-docker-images PR #2266 · 2026-05-15

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少系统工具/shadow-utils未安装` |
| 置信度 | 高 |

**根因**:
- 失败位置: `AI/mlflow/3.12.0/24.03-lts-sp3/Dockerfile` RUN groupadd 步骤
- 失败原因: openeuler:24.03-lts-sp3 基础镜像默认不包含 shadow-utils，`groupadd` 命令不存在

**原始报错**（如能获取）:
```
49.71 /bin/sh: line 1: groupadd: command not found
```

**修复方法**:
在 Dockerfile 的 dnf install 步骤中添加 `shadow` 包，使 groupadd/useradd 命令可用。

**涉及文件**:
- `AI/mlflow/3.12.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 shadow 依赖（+19）

---

## openeuler/openeuler-docker-images PR #2265 · 2026-05-15

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 404/Maven版本不在Apache CDN` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/netty/4.2.13/24.03-lts-sp3/Dockerfile` RUN wget Maven 步骤
- 失败原因: Apache CDN (`dlcdn.apache.org`) 只保留最新版本，Maven 3.9.14 已被更新版本替换，导致 404

**原始报错**（如能获取）:
```
> [3/7] RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.14/binaries/apache-maven-3.9.14-bin.tar.gz
0.110 --2026-05-11 02:46:31--  https://dlcdn.apache.org/maven/maven-3/3.9.14/binaries/...
404 Not Found
0.297 2026-05-11 02:46:31 ERROR 404: Not Found.
------
Dockerfile:12
```

**修复方法**:
将 Maven 下载源从 `dlcdn.apache.org` 改为 `repo.huaweicloud.com/apache/maven/maven-3/`，该镜像站保留历史版本。

**涉及文件**:
- `Others/netty/4.2.13/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，使用华为云镜像站下载 Maven（+28）

---

## openeuler/openeuler-docker-images PR #2264 · 2026-05-15

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少必需的二进制文件/COPY文件不存在` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Bigdata/logstash/9.4.0/24.03-lts-sp3/Dockerfile` COPY env2yaml 步骤
- 失败原因: Dockerfile 中 `COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml` 引用的二进制文件未包含在仓库中

**原始报错**（如能获取）:
```
#15 [11/13] COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml
#15 ERROR: failed to calculate checksum of ref kzw8fcgm9psa1a0kbi7cp9fx0::...: "/env2yaml/env2yaml-amd64": not found
```

**修复方法**:
在仓库中添加 `env2yaml/env2yaml-amd64` 和 `env2yaml/env2yaml-arm64` 二进制文件（随 Dockerfile 一同提交）。

**涉及文件**:
- `Bigdata/logstash/9.4.0/24.03-lts-sp3/env2yaml/env2yaml-amd64`: 新增二进制文件
- `Bigdata/logstash/9.4.0/24.03-lts-sp3/env2yaml/env2yaml-arm64`: 新增二进制文件
- `Bigdata/logstash/9.4.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile

---

## openeuler/openeuler-docker-images PR #2262 · 2026-05-15

| 字段 | 内容 |
|------|------|
| 失败类型 | `CI元数据缺失/image-list.yml条目遗漏` |
| 置信度 | 中 |

**根因**:
- 失败位置: `Bigdata/image-list.yml` CI 校验步骤
- 失败原因: 新增的 Bigdata 镜像未在 image-list.yml 中注册，CI 的镜像清单一致性检查失败

**原始报错**（如能获取）:
```
无法获取日志，基于 PR 描述推断（Bigdata/image-list.yml +7/-0）
```

**修复方法**:
向 `Bigdata/image-list.yml` 补充缺失的镜像条目（+7 行），使 CI 清单校验通过。

**涉及文件**:
- `Bigdata/image-list.yml`: 补充 7 条缺失的镜像条目

---

## openeuler/openeuler-docker-images PR #2212 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 403/镜像站访问被拒绝` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/gcc/16.1.0/24.03-lts-sp3/Dockerfile` RUN wget gcc 源码步骤
- 失败原因: 下载源 `mirrors.ustc.edu.cn` 返回 403 Forbidden，GCC 源码无法下载

**原始报错**（如能获取）:
```
wget https://mirrors.ustc.edu.cn/gnu/gcc/gcc-15.2.0/gcc-15.2.0.tar.gz
--2026-04-24 14:21:05--  https://mirrors.ustc.edu.cn/gnu/gcc/gcc-15.2.0/gcc-15.2.0.tar.gz
Connecting to mirrors.ustc.edu.cn|202.141.160.110|:443... connected.
HTTP request sent, awaiting response... 403 Forbidden
2026-04-24 14:21:06 ERROR 403: Forbidden.
```

**修复方法**:
将下载源从 `mirrors.ustc.edu.cn` 替换为 `mirrors.tuna.tsinghua.edu.cn`。

**涉及文件**:
- `Others/gcc/16.1.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，使用清华镜像站下载 GCC 源码（+43）

---

## openeuler/openeuler-docker-images PR #2211 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `BuildKit预定义变量冲突/BUILDARCH变量覆盖` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/spring-cloud/5.0.1/24.03-lts-sp3/Dockerfile` RUN wget JDK 步骤
- 失败原因: `BUILDARCH` 是 BuildKit 预定义的全局 ARG（值为 `amd64`/`arm64`），在 RUN 中将其赋值为自定义值（如 `x64`/`aarch64`）后失效，导致使用了 BuildKit 内置值构造错误的下载 URL，产生 404

**原始报错**（如能获取）:
```
> [4/5] RUN if [ "amd64" = "amd64" ]; then BUILDARCH="x64"; ...
0.285 HTTP request sent, awaiting response... 404 Not Found
0.353 2026-05-04 00:12:49 ERROR 404: Not Found.
```

**修复方法**:
将变量名从 `BUILDARCH` 改为其他自定义名称（如 `MY_ARCH` 或 `JAVA_ARCH`），避免与 BuildKit 预定义变量冲突。

**涉及文件**:
- `Others/spring-cloud/5.0.1/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，使用非冲突的变量名（+31）

---

## openeuler/openeuler-docker-images PR #2210 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少构建依赖/libxml2-devel未安装` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/wireshark/4.6.5/24.03-lts-sp3/Dockerfile` cmake 构建步骤
- 失败原因: cmake 找不到 LibXml2 库，wireshark 构建需要 libxml2-devel 但未在 Dockerfile 中安装

**原始报错**（如能获取）:
```
12.43 CMake Error at .../FindPackageHandleStandardArgs.cmake:230 (message):
12.43   Could NOT find LibXml2 (missing: LIBXML2_LIBRARY LIBXML2_INCLUDE_DIR)
12.43   (Required is at least version "2.9.7")
12.43   cmake/modules/FindLibXml2.cmake:110 (FIND_PACKAGE_HANDLE_STANDARD_ARGS)
12.43   CMakeLists.txt:1344 (find_package)
12.43 -- Configuring incomplete, errors occurred!
```

**修复方法**:
在 Dockerfile 的 dnf install 步骤中添加 `libxml2-devel` 包。

**涉及文件**:
- `Others/wireshark/4.6.5/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 libxml2-devel 依赖（+32）

---

## openeuler/openeuler-docker-images PR #2209 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `Patch应用失败/上游代码变更导致补丁冲突` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Database/tdengine/3.4.1.7/24.03-lts-sp3/Dockerfile` patch 应用步骤
- 失败原因: `cmake_curl.patch` 的第2个 hunk 应用失败（上游 cmake/external.cmake 文件已更新，偏移量不匹配）

**原始报错**（如能获取）:
```
#13 0.064 patching file cmake/external.cmake
#13 0.064 Hunk #1 succeeded at 937 (offset 43 lines).
#13 0.064 patch unexpectedly ends in middle of line
#13 0.064 Hunk #2 FAILED at 1099.
#13 0.064 1 out of 2 hunks FAILED -- saving rejects to file cmake/external.cmake.rej
#13 ERROR: process "/bin/sh -c patch -Np1 < cmake_curl.patch && ./build.sh" did not complete successfully: exit code: 1
```

**修复方法**:
针对新版上游代码重新生成 `cmake_curl.patch` 补丁文件，并调整编译参数。

**涉及文件**:
- `Database/tdengine/3.4.1.7/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile（+19）
- `Database/tdengine/3.4.1.7/24.03-lts-sp3/cmake_curl.patch`: 更新后的补丁文件（+13）
- `Database/tdengine/3.4.1.7/24.03-lts-sp3/build.sh`: 构建脚本（+7）

---

## openeuler/openeuler-docker-images PR #2208 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `Shell变量语法错误/$nproc应为$(nproc)` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/snort3/3.12.2.0/24.03-lts-sp3/Dockerfile` make 构建步骤
- 失败原因: Dockerfile 中使用了 `$nproc` 作为变量引用，但 `nproc` 是命令而非变量，正确写法应为 `$(nproc)` 命令替换

**原始报错**（如能获取）:
```
make: *** [Makefile:156: all] Error 2
[33m1 warning found (use --debug to expand):
- UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 16)
```

**修复方法**:
将 Dockerfile 中的 `$nproc` 改为 `$(nproc)`，使构建时能正确获取 CPU 核心数并行编译。

**涉及文件**:
- `Others/snort3/3.12.2.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，修正 $(nproc) 语法（+21）

---

## openeuler/openeuler-docker-images PR #2207 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `Maven版本约束不满足/版本过低` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Database/neo4j/2026.04.0/24.03-lts-sp3/Dockerfile` mvn build 步骤
- 失败原因: neo4j 2026.04.0 的 maven-enforcer-plugin 要求 Maven >= 3.9.11，但 Dockerfile 安装的是 Maven 3.9.1

**原始报错**（如能获取）:
```
#8 69.10 [ERROR] Rule 5: org.apache.maven.enforcer.rules.version.RequireMavenVersion failed with message:
#8 69.10 [ERROR] Detected Maven Version: 3.9.1 is not in the allowed range [3.9.11,).
#8 69.10 [ERROR] -> [Help 1]
#8 ERROR: process "/bin/sh -c git clone -b ${VERSION} https://github.com/neo4j/neo4j.git && cd neo4j && mvn clean install ..." did not complete successfully: exit code: 1
```

**修复方法**:
将 Dockerfile 中 Maven 版本从 3.9.1 升级至 3.9.14。

**涉及文件**:
- `Database/neo4j/2026.04.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，Maven 升级至 3.9.14（+34）

---

## openeuler/openeuler-docker-images PR #2206 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少必需的二进制文件/COPY文件不存在` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Bigdata/logstash/9.3.4/24.03-lts-sp3/Dockerfile` COPY env2yaml 步骤
- 失败原因: 与 PR #2264 同类问题——env2yaml 架构相关二进制文件未包含在仓库中

**原始报错**（如能获取）:
```
#15 [11/13] COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml
#15 ERROR: failed to calculate checksum of ref ...: "/env2yaml/env2yaml-amd64": not found
```

**修复方法**:
在仓库中添加 `env2yaml/env2yaml-amd64` 和 `env2yaml/env2yaml-arm64` 二进制文件。

**涉及文件**:
- `Bigdata/logstash/9.3.4/24.03-lts-sp3/env2yaml/env2yaml-amd64`: 新增二进制文件
- `Bigdata/logstash/9.3.4/24.03-lts-sp3/env2yaml/env2yaml-arm64`: 新增二进制文件
- `Bigdata/logstash/9.3.4/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile（+47）

---

## openeuler/openeuler-docker-images PR #2205 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `CMake缺少依赖/Boost库未配置` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Database/mysql/9.7.0/24.03-lts-sp3/Dockerfile` cmake 配置步骤
- 失败原因: cmake 配置时找不到 CURL 库（实际根因是 Boost 依赖未正确配置，MySQL 编译需通过 `-DDOWNLOAD_BOOST` 获取 Boost）

**原始报错**（如能获取）:
```
#8 185.6 -- Could NOT find CURL (missing: CURL_LIBRARY CURL_INCLUDE_DIR)
#8 185.6 -- CURL_INCLUDE_DIR =
#8 185.6 -- Configuring incomplete, errors occurred!
```

**修复方法**:
在 cmake 构建参数中添加 `-DDOWNLOAD_BOOST=1 -DWITH_BOOST=/tmp/boost`，让 MySQL 自动下载并使用 Boost 库。

**涉及文件**:
- `Database/mysql/9.7.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 Boost cmake 参数（+48）

---

## openeuler/openeuler-docker-images PR #2204 · 2026-05-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `requirements文件路径变更/pip找不到依赖文件` |
| 置信度 | 高 |

**根因**:
- 失败位置: `AI/vllm-cpu/0.20.1/24.03-lts-sp3/Dockerfile` pip install 步骤
- 失败原因: vllm-cpu 上游仓库重组了目录结构，`requirements/cpu-build.txt` 移动至 `requirements/build/cpu.txt`

**原始报错**（如能获取）:
```
#12 [build 1/2] RUN pip install -r requirements/cpu-build.txt
#12 0.668 ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements/cpu-build.txt'
#12 ERROR: process "/bin/sh -c pip install -r requirements/cpu-build.txt" did not complete successfully: exit code: 1
```

**修复方法**:
将 Dockerfile 中的 requirements 路径从 `requirements/cpu-build.txt` 改为 `requirements/build/cpu.txt`。

**涉及文件**:
- `AI/vllm-cpu/0.20.1/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，修正 requirements 路径（+52）

---

## openeuler/openeuler-docker-images PR #2164 · 2026-04-24

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少系统工具/shadow-utils未安装` |
| 置信度 | 高 |

**根因**:
- 失败位置: `AI/mlflow/3.11.1/24.03-lts-sp3/Dockerfile` RUN groupadd 步骤
- 失败原因: 与 PR #2266 同类问题，openeuler:24.03-lts-sp3 基础镜像默认不含 shadow-utils

**原始报错**（如能获取）:
```
49.71 /bin/sh: line 1: groupadd: command not found
```

**修复方法**:
在 Dockerfile 的 dnf install 步骤中添加 `shadow` 包。

**涉及文件**:
- `AI/mlflow/3.11.1/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 shadow 依赖（+19）

---

## openeuler/openeuler-docker-images PR #2163 · 2026-04-24

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少必需的二进制文件/COPY文件不存在` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Bigdata/logstash/9.3.3/24.03-lts-sp3/Dockerfile` COPY env2yaml 步骤
- 失败原因: 与 PR #2264/#2206 同类问题，env2yaml 二进制文件未包含在仓库中

**原始报错**（如能获取）:
```
#16 [11/13] COPY env2yaml/env2yaml-amd64 /usr/local/bin/env2yaml
#16 ERROR: failed to calculate checksum of ref ydytjq0j10wdx7q8kbvosbxmt::...: "/env2yaml/env2yaml-amd64": not found
```

**修复方法**:
在仓库中添加 `env2yaml/env2yaml-amd64` 和 `env2yaml/env2yaml-arm64` 二进制文件。

**涉及文件**:
- `Bigdata/logstash/9.3.3/24.03-lts-sp3/env2yaml/env2yaml-amd64`: 新增二进制文件
- `Bigdata/logstash/9.3.3/24.03-lts-sp3/env2yaml/env2yaml-arm64`: 新增二进制文件
- `Bigdata/logstash/9.3.3/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile（+47）

---

## openeuler/openeuler-docker-images PR #2162 · 2026-04-24

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少构建依赖/PCRE库未安装` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Cloud/nginx/1.30.0/24.03-lts-sp3/Dockerfile` configure 步骤
- 失败原因: nginx 编译时 `--with-http_rewrite_module` 需要 PCRE 库，但 Dockerfile 未安装 pcre/pcre-devel

**原始报错**（如能获取）:
```
#7 104.4 ./configure: error: the HTTP rewrite module requires the PCRE library.
#7 104.4 You can either disable the module by using --without-http_rewrite_module
#7 104.4 option, or install the PCRE library into the system, or build the PCRE library
#7 104.4 statically from the source with nginx by using --with-pcre=<path> option.
```

**修复方法**:
在 Dockerfile 的 dnf install 步骤中添加 `pcre` 和 `pcre-devel` 包。

**涉及文件**:
- `Cloud/nginx/1.30.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 pcre/pcre-devel 依赖（+46）

---

## openeuler/openeuler-docker-images PR #2105 · 2026-04-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 404/JDK版本不存在` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp3/Dockerfile` RUN wget JDK 步骤
- 失败原因: Adoptium JDK 11.0.28_6 在清华镜像站上不存在，下载返回 404（同时也受 BUILDARCH 变量冲突影响，实际下载 URL 中使用了错误路径）

**原始报错**（如能获取）:
```
#10 0.087 --2026-04-06 01:14:48--  https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/x64/linux/OpenJDK11U-jre_x64_linux_hotspot_11.0.28_6.tar.gz
#10 0.317 Connecting to mirrors.tuna.tsinghua.edu.cn|101.6.15.130|:443... connected.
#10 0.503 HTTP request sent, awaiting response... 404 Not Found
#10 0.586 2026-04-06 01:14:49 ERROR 404: Not Found.
```

**修复方法**:
将 JDK 版本从 11.0.28_6 升级至 11.0.30_7（已在 Adoptium 上发布的版本）。

**涉及文件**:
- `Bigdata/kyuubi/1.11.1/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，JDK 升级至 11.0.30_7（+62）

---

## openeuler/openeuler-docker-images PR #2104 · 2026-04-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `Patch应用失败/上游代码变更导致补丁冲突` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Database/tdengine/3.4.1.1/24.03-lts-sp3/Dockerfile` patch 应用步骤
- 失败原因: 与 PR #2209 同类问题，cmake_curl.patch 第2个 hunk 因上游代码行号变化而应用失败

**原始报错**（如能获取）:
```
#13 0.072 patching file cmake/external.cmake
#13 0.072 Hunk #1 succeeded at 937 (offset 43 lines).
#13 0.072 patch unexpectedly ends in middle of line
#13 0.072 Hunk #2 FAILED at 1099.
#13 0.072 1 out of 2 hunks FAILED -- saving rejects to file cmake/external.cmake.rej
#13 ERROR: process did not complete successfully: exit code: 1
```

**修复方法**:
针对 tdengine 3.4.1.1 的上游代码重新生成 cmake_curl.patch，并更新编译参数。

**涉及文件**:
- `Database/tdengine/3.4.1.1/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile（+19）
- `Database/tdengine/3.4.1.1/24.03-lts-sp3/cmake_curl.patch`: 重新生成的补丁文件（+13）
- `Database/tdengine/3.4.1.1/24.03-lts-sp3/build.sh`: 构建脚本（+7）

---

## openeuler/openeuler-docker-images PR #2102 · 2026-04-07

| 字段 | 内容 |
|------|------|
| 失败类型 | `Maven版本约束不满足/版本过低` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Database/neo4j/2026.03.1/24.03-lts-sp3/Dockerfile` mvn build 步骤
- 失败原因: 与 PR #2207 同类问题，neo4j 2026.03.1 要求 Maven >= 3.9.11，Dockerfile 中为 3.9.1

**原始报错**（如能获取）:
```
#8 69.10 [ERROR] Detected Maven Version: 3.9.1 is not in the allowed range [3.9.11,).
#8 69.10 [ERROR] Rule 5: org.apache.maven.enforcer.rules.version.RequireMavenVersion failed
#8 ERROR: process "/bin/sh -c git clone -b ${VERSION} ... && mvn clean install ..." did not complete successfully: exit code: 1
```

**修复方法**:
将 Dockerfile 中 Maven 版本从 3.9.1 升级至 3.9.14。

**涉及文件**:
- `Database/neo4j/2026.03.1/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，Maven 升级至 3.9.14（+33）

---

## openeuler/openeuler-docker-images PR #2100 · 2026-04-07

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 404/Maven版本不在Apache CDN` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/netty/4.2.12/24.03-lts-sp3/Dockerfile` RUN wget Maven 步骤
- 失败原因: Apache CDN (`dlcdn.apache.org`) 不再托管 Maven 3.9.12（已被更新版本替换），返回 404

**原始报错**（如能获取）:
```
#9 0.111 --2026-04-06 07:28:51--  https://dlcdn.apache.org/maven/maven-3/3.9.12/binaries/apache-maven-3.9.12-bin.tar.gz
#9 0.175 HTTP request sent, awaiting response... 404 Not Found
#9 0.177 2026-04-06 07:28:51 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c wget .../apache-maven-${MAVEN_VERSION}-bin.tar.gz ..." did not complete successfully: exit code: 8
```

**修复方法**:
将 Dockerfile 中 `ARG MAVEN_VERSION=3.9.12` 改为 `ARG MAVEN_VERSION=3.9.14`（Apache CDN 当前可用版本）。

**涉及文件**:
- `Others/netty/4.2.12/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，Maven 升级至 3.9.14（+28）

---

## openeuler/openeuler-docker-images PR #1934 · 2026-02-24

| 字段 | 内容 |
|------|------|
| 失败类型 | `x86_64编译错误/AVX512BF16指令集缺少fallback` |
| 置信度 | 高 |

**根因**:
- 失败位置: `AI/vllm-cpu/0.16.0/24.03-lts-sp3/Dockerfile` 编译 csrc/cpu/mla_decode.cpp 步骤
- 失败原因: `KernelVecType<c10::BFloat16>` 只有 `__AVX512BF16__`/`__s390x__`/`__aarch64__` 三个特化，无 `#else` 分支，导致在普通 x86_64（无 AVX512BF16）上 `qk_vec_type` 解析为 `void`

**原始报错**（如能获取）:
```
error: incomplete type 'qk_vec_type' {aka 'void'} used in nested name specifier
```

**修复方法**:
回溯移植 vllm-project/vllm PR #34052 的修复：将两个相同的 `#elif` 分支合并为单一 `#else`，使所有非 AVX512BF16 平台共用 `FP32Vec16` 计算路径。以 Python patch 步骤在 Dockerfile 的 `git clone` 后应用。

**涉及文件**:
- `AI/vllm-cpu/0.16.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，包含 Python patch 步骤修复 AVX512BF16 fallback（+55）

---

## openeuler/openeuler-docker-images PR #1933 · 2026-02-24

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少构建依赖/protobuf-c-compiler未安装` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/rsyslog/8.2602.0/24.03-lts-sp3/Dockerfile` ./configure 步骤
- 失败原因: rsyslog 8.2602.0 新增了对 protobuf-c 的依赖，但 Dockerfile 未安装 `protobuf-c-compiler` 和 `protobuf-c-devel`

**原始报错**（如能获取）:
```
./configure: error: protoc-c not found. Please install protobuf-c-compiler package.
```

**修复方法**:
在 Dockerfile 的 dnf install 步骤中添加 `protobuf-c-compiler` 和 `protobuf-c-devel`。

**涉及文件**:
- `Others/rsyslog/8.2602.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 protobuf-c 相关依赖（+21）

---

## openeuler/openeuler-docker-images PR #1932 · 2026-02-24

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 404/软件包版本不存在` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Database/phoenix/5.3.0/24.03-lts-sp3/Dockerfile` RUN wget 步骤
- 失败原因: `phoenix-hbase-2.4-5.3.0-bin.tar.gz` 不存在——Phoenix 5.3.0 已放弃 HBase 2.4 支持，且 `dlcdn.apache.org` 只托管最新版本

**原始报错**（如能获取）:
```
无法获取日志，根因来自 PR 描述：phoenix-hbase-2.4-5.3.0-bin.tar.gz does not exist
```

**修复方法**:
1. 将下载源从 `dlcdn.apache.org` 改为 `archive.apache.org/dist`（保留历史版本）
2. 将 HBase 版本从 `hbase-2.4` 改为 `hbase-2.5`（Phoenix 5.3.0 支持的版本）

**涉及文件**:
- `Database/phoenix/5.3.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，使用 archive.apache.org + hbase-2.5（+9）

---

## openeuler/openeuler-docker-images PR #1884 · 2026-02-10

| 字段 | 内容 |
|------|------|
| 失败类型 | `下载URL 404/Maven版本不在Apache CDN` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/netty/4.2.10/24.03-lts-sp3/Dockerfile` RUN wget Maven 步骤
- 失败原因: Maven 3.9.11 在 Apache CDN 上不存在（只有 3.8.9 和 3.9.12），x86_64 和 aarch64 均报 HTTP 404

**原始报错**（如能获取）:
```
curl -I https://dlcdn.apache.org/maven/maven-3/3.9.11/binaries/apache-maven-3.9.11-bin.tar.gz
# HTTP 404 Not Found
```

**修复方法**:
将 Dockerfile 中 `MAVEN_VERSION` 从 3.9.11 改为 3.9.12，并将 Maven 文件名中的硬编码版本改为变量 `${MAVEN_VERSION}`。

**涉及文件**:
- `Others/netty/4.2.10/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，MAVEN_VERSION 升级至 3.9.12（+28）

---

## openeuler/openeuler-docker-images PR #1858 · 2026-02-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `缺少系统工具/shadow-utils未安装` |
| 置信度 | 高 |

**根因**:
- 失败位置: `AI/mlflow/3.9.0/24.03-lts-sp3/Dockerfile` groupadd/useradd 步骤
- 失败原因: openeuler:24.03-lts-sp3 基础镜像默认不包含 shadow-utils 包，`groupadd`/`useradd` 命令不存在

**原始报错**（如能获取）:
```
groupadd: command not found
(x86_64 和 aarch64 均失败)
```

**修复方法**:
在 Dockerfile 第一个 RUN 指令中与 `python3-pip` 一并安装 `shadow-utils`，使用户管理命令在使用前可用。

**涉及文件**:
- `AI/mlflow/3.9.0/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，添加 shadow-utils 依赖（+19）

---

## openeuler/openeuler-docker-images PR #1857 · 2026-02-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `RPM包不存在/上游停止发布RPM` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Cloud/grafana-agent/0.44.7/24.03-lts-sp3/Dockerfile` RPM 下载/安装步骤
- 失败原因: grafana-agent RPM 包在 v0.44.2 后停止发布，v0.44.7 无可用 RPM，CI 下载失败

**原始报错**（如能获取）:
```
无法获取日志，根因来自 PR 描述：grafana-agent v0.44.7 does not publish RPM packages (RPM releases stopped after v0.44.2)
```

**修复方法**:
改用多阶段 Docker 构建：直接从官方 `grafana/agent:v0.44.7` Docker 镜像中 COPY grafana-agent 二进制文件，替代从不存在的 RPM 安装。

**涉及文件**:
- `Cloud/grafana-agent/0.44.7/24.03-lts-sp3/Dockerfile`: 新增多阶段 Dockerfile，从官方镜像复制二进制（+12）

---

## openeuler/openeuler-docker-images PR #1856 · 2026-02-05

| 字段 | 内容 |
|------|------|
| 失败类型 | `pip版本不兼容/pip 26.0移除API` |
| 置信度 | 高 |

**根因**:
- 失败位置: `Others/spdk/26.01/24.03-lts-sp3/Dockerfile` pkgdep.sh 执行步骤
- 失败原因: SPDK v26.01 的 `scripts/pkgdep/rhel.sh` 创建 Python venv 时使用 `--upgrade-deps` 将 pip 升级到 26.0，而 pip-tools 7.5.2 调用了 pip 26.0 中已被删除的 `PackageFinder.allow_all_prereleases` 属性

**原始报错**（如能获取）:
```
AttributeError: 'PackageFinder' object has no attribute 'allow_all_prereleases'
(x86_64 和 aarch64 的 check_build 均失败)
```

**修复方法**:
在 Dockerfile 中，于运行 `pkgdep.sh` 前添加一步 `sed` 命令，从 `rhel.sh` 中删除 `--upgrade-deps` 参数，使 venv 保持使用系统 pip 版本（与 pip-tools 7.5.2 兼容）。

**涉及文件**:
- `Others/spdk/26.01/24.03-lts-sp3/Dockerfile`: 新增 Dockerfile，含 sed 去除 --upgrade-deps（+27）

---

## openeuler/openeuler-docker-images PR #1768 · 2026-01-08

| 字段 | 内容 |
|------|------|
| 失败类型 | `Dockerfile构建错误（推断）` |
| 置信度 | 低 |

**根因**:
- 失败位置: `Others/spring-cloud/5.0.0/24.03-lts-sp3/Dockerfile`
- 失败原因: PR #1756 的 CI 构建失败，具体错误信息无法从 PR 描述中获取；通过 Dockerfile 更新修复

**原始报错**（如能获取）:
```
无法获取日志
```

**修复方法**:
更新 `Others/spring-cloud/5.0.0/24.03-lts-sp3/Dockerfile`（具体修改内容基于文件 diff 推断，+31 行新增）。

**涉及文件**:
- `Others/spring-cloud/5.0.0/24.03-lts-sp3/Dockerfile`: 新增/重写 Dockerfile（+31）


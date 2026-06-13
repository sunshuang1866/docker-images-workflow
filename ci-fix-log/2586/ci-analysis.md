# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨架构编译标志不兼容
- 新模式症状关键词: `unrecognized command-line option`, `-m64`, `-mavx`, `-msse4`, `-mpopcnt`, `aarch64`, `g++: error`, `makefile.inc`

## 根因分析

### 直接错误
```
#9 106.4 g++ -fPIC -m64 -Wall -g -O3 -mavx -msse4 -mpopcnt -fopenmp -Wno-sign-compare -std=c++11 -fopenmp -c hamming.cpp -o hamming.o  
#9 106.4 g++: error: unrecognized command-line option '-m64'
#9 106.4 g++: error: unrecognized command-line option '-mavx'
#9 106.4 g++: error: unrecognized command-line option '-msse4'
#9 106.4 g++: error: unrecognized command-line option '-mpopcnt'
#9 106.4 make: *** [Makefile:43: hamming.o] Error 1
```

### 根因定位
- 失败位置: `AI/faiss/20180223/24.03-lts-sp3/Dockerfile`:19 (RUN 命令内的 make 步骤)
- 失败原因: faiss v20180223 的 `example_makefiles/makefile.inc.Linux` 硬编码了 x86_64 专属 CPU 标志（`-m64`、`-mavx`、`-msse4`、`-mpopcnt`），在 aarch64 架构上构建时，aarch64 的 g++ 编译器不认识这些选项，直接报错退出。

### 与 PR 变更的关联
PR 新增了一个从头编译 faiss v20180223 的 Dockerfile。Dockerfile 第 19 行的 `RUN` 命令中：

```
cp example_makefiles/makefile.inc.Linux makefile.inc
```

直接复制了面向 x86_64 Linux 的 Makefile 配置模板，未根据 `TARGETARCH` 对编译标志做任何架构适配。在 aarch64 构建节点上，`-m64`、`-mavx`、`-msse4`、`-mpopcnt` 这些 x86 指令集标志无法被 aarch64 g++ 识别，导致编译失败。这是本次 PR 新增内容直接引入的问题。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 中，`cp example_makefiles/makefile.inc.Linux makefile.inc` 之后，根据 `TARGETARCH` 变量用 `sed` 移除不兼容的编译标志。当 `TARGETARCH` 为 `arm64` 时，从 makefile.inc 中删除 `-m64`、`-mavx`、`-msse4`、`-mpopcnt` 等 x86 专属标志，使编译命令仅保留架构无关的选项（`-fPIC`、`-Wall`、`-g`、`-O3`、`-fopenmp`、`-std=c++11` 等）。

### 方向 2（置信度: 低）
考虑 faiss v20180223 版本过于古老（2018年2月），该版本的 Makefile 构建系统可能从根本上不支持 aarch64。如果移除 x86 标志后仍出现其他架构相关编译错误，可能需要升级 faiss 到支持 aarch64 的较新版本（如已有的 1.14.1），或放弃 aarch64 构建仅支持 amd64。

## 需要进一步确认的点
- aarch64 构建节点上，移除 `-m64`/`-mavx`/`-msse4`/`-mpopcnt` 后，faiss v20180223 是否还有其他 aarch64 不兼容的代码（如内联汇编、x86 intrinsic 等）
- `example_makefiles/makefile.inc.Linux` 的完整内容，确认还有哪些标志需要按架构条件处理

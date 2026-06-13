# CI 失败分析报告

## 基本信息
- PR: #2586 — 【自动升级】faiss容器镜像升级至20180223版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 编译标志架构不兼容
- 新模式症状关键词: unrecognized command-line option, -m64, -mavx, -msse4, -mpopcnt, aarch64, g++

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
- 失败位置: `/tmp/faiss/Makefile:43`
- 失败原因: faiss v20180223 的 Makefile（基于 `example_makefiles/makefile.inc.Linux`）硬编码了 x86_64 专用编译器标志（`-m64`、`-mavx`、`-msse4`、`-mpopcnt`），在 aarch64 架构上编译时 g++ 无法识别这些选项，导致编译失败。

### 与 PR 变更的关联
PR #2586 新增了 faiss 20180223 版本的 Dockerfile。虽然 PR diff 显示的 Dockerfile 采用 conda 直接安装预编译包的方式（`conda install faiss-cpu=${VERSION}`），但 CI 实际执行的构建包含从 GitHub 克隆 faiss v20180223 源码并手动编译的步骤。faiss v20180223 是 2018 年的极旧版本，其构建系统从未考虑过 ARM/AARCH64 架构支持，`makefile.inc.Linux` 的编译器标志完全面向 x86_64。

**注意**：PR diff 中的 Dockerfile 内容与 CI 日志中实际执行的构建步骤存在显著差异——diff 显示的是 conda 安装方式（无编译环节），而 CI 日志显示的是 `git clone` + `make` 的源码编译流程。此差异需要在仓库中进一步确认实际被构建的 Dockerfile 内容。

## 修复方向

### 方向 1（置信度: 高）
faiss 官方 conda channel（pytorch / conda-forge）提供的 `faiss-cpu=20180223` 预编译包可能已经包含 aarch64 版本，且 conda 会自动处理平台兼容性。优先确保 Dockerfile 使用 conda 安装方式，避免手动编译老旧 faiss 源码。如果 conda channel 中 `faiss-cpu=20180223` 没有可用的 aarch64 预编译包，则需要考虑以下两种替代策略：

### 方向 2（置信度: 中）
如果必须通过源码编译 faiss v20180223，需要在 `make` 前修改 `makefile.inc`，移除或条件化 x86 专用标志。具体做法：在 bash -c 块中，在 `make` 之前加入 sed 命令，根据目标架构（`TARGETARCH`）移除 `-m64`、`-mavx`、`-msse4`、`-mpopcnt` 等 x86-only 标志。

### 方向 3（置信度: 低）
考虑放弃 faiss v20180223 这一极旧版本，改用已有成功构建记录的版本（如已存在的 1.14.1）。v20180223 是 2018 年的版本，代码早已停更，在 ARM 架构上的兼容性风险高，维护成本远超其价值。

## 需要进一步确认的点
1. CI 实际执行的构建步骤与 PR diff 不一致：diff 中 Dockerfile 仅 21 行且使用 conda 安装，但 CI 日志显示执行的是包含 `yum install` 和 `git clone` + `make` 的源码编译 Dockerfile。需要确认仓库中 `AI/faiss/20180223/24.03-lts-sp3/Dockerfile` 的实际内容。
2. 确认 conda 官方 channel 中 `faiss-cpu=20180223` 是否提供 aarch64/linux-aarch64 预编译包，可使用 `conda search faiss-cpu=20180223 --info` 验证。
3. 该失败是否同时发生在 amd64 架构——当前日志仅显示 aarch64 构建过程，x86_64 架构可能编译成功（因为 `-m64 -mavx -msse4 -mpopcnt` 在 x86_64 上是合法选项）。

# 修复摘要

## 修复的问题
移除 `./scripts/install_deps.sh` 调用，改为在 Dockerfile 中直接安装 openEuler 可用的等效构建依赖包，解决上游脚本对 CentOS/RHEL 专有包的依赖导致的构建失败。

## 修改的文件
- `Database/milvus/2.6.0/24.03-lts-sp4/Dockerfile`: 
  1. 第 12 行在 `yum install` 中新增 `automake autoconf libtool m4 python3-devel curl` 六个包
  2. 第 24 行移除 `./scripts/install_deps.sh &&` 调用

## 修复逻辑
CI 失败的直接原因是上游 Milvus `install_deps.sh`（v2.6.0 版本）被设计为 CentOS/RHEL 专用，内部通过 yum 安装 `epel-release`、`centos-release-scl-rh`、`devtoolset-11-*`、`llvm-toolset-11.0-*`、`lcov` 等 CentOS SCL 仓库中的包，并通过 `scl_source` 配置环境，这些在 openEuler 24.03-LTS-SP4 上均不可用，导致 yum 返回非零退出码，RUN 指令的 `&&` 链中断。

修复方案采用分析报告的"方向 1"（高置信度）：跳过不兼容的上游脚本，将其中必要的构建工具（`automake`、`autoconf`、`libtool`、`m4`、`python3-devel`、`curl`）添加到 Dockerfile 已有的 `yum install` 阶段。以下依赖已由原 Dockerfile 覆盖，无需额外处理：
- gcc/g++/gfortran（系统版本，无需求助于 devtoolset SCL）
- cmake、make、git、wget、ninja 等基础构建工具
- openblas-devel、libaio、libuuid-devel 等运行时/编译库
- Go、Rust、conan 已在前序 RUN 层单独安装

## 潜在风险
1. `install_deps.sh` 中安装的 `ccache`、`lcov`、`clang`/`clang-tools-extra` 在本次修复中未添加，这些属于编译器缓存/代码覆盖率/代码格式化工具，预计不影响 `make build-cpp` 和 `make build-go` 的成功执行。若后续构建因此失败，可按需补充对应包名。
2. `install_deps.sh` 中的 cmake 版本检查（要求 >= 3.26）未保留。openEuler 24.03-LTS-SP4 预期已包含 cmake >= 3.26，若实际版本偏低，需在各 RUN 层之间插入 cmake 升级步骤。
3. `install_deps.sh` 会升级 Rust 到 1.83 并重装 conan==1.64.1，Dockerfile 使用 Rust 1.73 和 conan==1.61.0，版本差异可能影响编译兼容性。
# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式10 (缺少构建依赖) + 模式18 (git 浅克隆与 commit hash checkout 不兼容)
- 新模式标题: 运行时包名错误
- 新模式症状关键词: boost-foundation, No match for argument, yum install

## 根因分析

### 直接错误

```
#12 [7/8] RUN yum -y install fuse3-libs openssl-libs lz4 xz-libs double-conversion libdwarf libunwind libaio gflags glog gperftools boost-foundation boost-filesystem boost-system boost-program-options libuv &&     yum clean all
...
#12 25.82 No match for argument: boost-foundation
#12 25.84 Error: Unable to find a match: boost-foundation
#12 ERROR: process "/bin/sh -c yum -y install fuse3-libs ... boost-foundation ..." did not complete successfully: exit code: 1
------
Dockerfile:41
Error: Unable to find a match: boost-foundation
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:41
- 失败原因: 新增的 3FS Dockerfile 在运行时库安装步骤（step #12）中引用了不存在的包名 `boost-foundation`，openEuler yum 仓库中无此包名，`yum install` 返回 exit code 1

### 与 PR 变更的关联

本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（52 行新文件），该 Dockerfile 是全新的，所有错误均源于此文件中的依赖声明不正确。具体而言：

1. **直接失败（Dockerfile:41）**：运行时阶段 `yum install boost-foundation` 失败 — 该包名在 openEuler 仓库中不存在。openEuler 24.03-LTS-SP3 的 boost 库运行时包命名规范为 `boost-<component>` 而非 `boost-foundation`，正确的包名可能为 `boost`（元包）或无需单独安装（boost-filesystem/system/program-options 的运行时 `.so` 已随 `boost-devel` 安装阶段被保留）。

2. **cmake 配置阶段错误（Dockerfile:22-37 行的 RUN 块内）**：build 阶段 cmake 配置时报 `Could NOT find libevent`（位于 `third_party/folly/build/fbcode_builder/CMake/FindLibEvent.cmake:68`），folly 子模块找不到 `libevent` 导致配置失败。日志显示 `CMake Error` + `Configuring incomplete, errors occurred!`，但该 RUN 步骤未因此中断（`#10 DONE 78.5s`），说明 cmake 以某种方式容错继续。`libevent-devel` 未出现在 Dockerfile 的 build 依赖安装列表中（第 4 行 RUN），属于缺少构建依赖（模式10）。

3. **git 浅克隆 + commit checkout 问题（模式18）**：Dockerfile:22-24 行使用 `git clone --depth 1 ...` 后执行 `git checkout ${VERSION} 2>/dev/null || true`，`--depth 1` 浅克隆只包含最新提交，而 `|| true` 静默抑制 checkout 失败，导致若 `22fca04` 不是默认分支 HEAD 则无法真正切换到目标版本。

## 修复方向

### 方向 1（置信度: 高）
`boost-foundation` 包名不存在。修正方案：从运行时 `yum install` 列表中移除 `boost-foundation`，或替换为 openEuler 仓库中实际存在的 boost 运行时包名（如 `boost`）。同时确认 boost 相关的 `.so` 文件在 `yum -y remove wget gcc make`（step #11）之后是否仍然存在于 `/usr/lib64/` 下 — 若 `yum remove` 误删了 boost 运行时库，需调整 `remove` 清理范围（去掉 `gcc make` 的级联删除，或手动指定 remove 列表避免误删 boost）。

### 方向 2（置信度: 中）
build 阶段缺少 `libevent-devel` 依赖。修正方案：在 Dockerfile 第 4 行的 `yum install` 命令中追加 `libevent-devel`，以解决 folly 子模块的 cmake 配置错误。同时复查 folly 是否还有其他未声明的依赖（参考 folly 官方构建文档 `fbcode_builder` 的依赖列表）。

### 方向 3（置信度: 中）
模式18 — `--depth 1` 浅克隆与 commit hash checkout 不兼容。修正方案：将 `git checkout ${VERSION} 2>/dev/null || true` 改为先 `git fetch origin ${VERSION} --depth 1` 再 `git checkout FETCH_HEAD`，或去掉 `--depth 1` 改为 `--depth 50` 增加可访问历史范围；同时去掉 `2>/dev/null || true` 让 checkout 失败时构建显式终止，避免静默构建错误版本。

## 需要进一步确认的点

1. **步骤 #10 cmake 为何未导致构建中断**：日志显示 `CMake Error` + `Configuring incomplete, errors occurred!` 但步骤仍标记为 `DONE`。需确认该 RUN 命令在 Docker BuildKit 下的实际退出码，以及 cmake 是否因 folly 为 optional dependency 而归零退出码。如果 cmake 确实失败但被掩盖，3FS 可能根本没有被编译（`cmake --build` 未执行），后续 `cp /tmp/3fs/build/bin/* /opt/3fs/bin/` 会复制空目录，最终镜像缺少二进制文件。

2. **`boost-foundation` 在 openEuler 24.03-LTS-SP3 中的实际对应包名**：需要在目标容器环境中执行 `yum search boost` 或查阅 openEuler 包仓库确认 boost 运行时的正确包名（如 `boost` 元包、或完全不需单独安装，因为 boost 是 header-only 模板库为主，`boost-devel` 安装的 `.so` 在 `yum remove` 后可能需要重新安装 `boost` 元包来恢复被级联删除的运行时库）。

3. **`yum -y remove wget gcc make` 的级联副作用**：日志显示该命令实际删除了 23 个包（包括 `clang`、`clang-libs`、`gcc-c++`、`binutils`、`glibc-devel`、`kernel-headers`、`libstdc++-devel` 等），部分被删除的包（如 `boost` 相关运行时库）可能正是 step #12 试图重新安装 `boost-foundation` 的原因 — 需要确认 remove 步骤是否误删了 boost 运行时库，以及修复后 step #12 的 yum install 是否仍有必要。

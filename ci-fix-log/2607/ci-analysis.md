# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: getdeps-libaio构建失败
- 新模式症状关键词: Assessing libaio, getdeps.py, exit code: 1, fbthrift

## 根因分析

### 直接错误
```
#11 340.9 Building googletest...
#11 340.9 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ..." did not complete successfully: exit code: 1
------
Dockerfile:18
--------------------
  18 | >>> RUN git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && \
  ...
  23 | >>>     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`:23（getdeps.py 构建步骤）
- 失败原因: fbcode_builder 的 `getdeps.py` 在构建 libaio 依赖时失败（exit code 1）。日志在 `Assessing libaio...` 之后被截断，未见具体编译/配置错误信息。

### 与 PR 变更的关联

此 PR 新增了 fbthrift v2026.06.15.00 的 Dockerfile 及配套文件：
1. **Dockerfile** (新增) — 定义了完整的 fbthrift 构建流程，包含 `getdeps.py` 调用
2. **fix_getdeps.py** (新增) — 两个修复：(a) 将 `openeuler` 加入发行版识别列表；(b) 跳过 libaio 的哈希校验
3. **libaio-libaio-0.3.113.tar.gz** (新增) — 预下载的 libaio 源码包

构建流程中，getdeps 依次构建了 ninja、benchmark、zlib、zstd、fmt、boost、fast_float、gflags、glog、googletest 均成功，但在处理 libaio 时失败。虽然 `fix_getdeps.py` 跳过了哈希校验，但 libaio 的评估/构建步骤仍然失败。可能原因：

- libaio 的构建依赖（如基础编译工具链之外的特定依赖）未被 `dnf install` 覆盖
- libaio 源码与 GCC 12.3.1 / openEuler 24.03 环境存在兼容性问题
- getdeps 对 libaio 的目录/文件名约定与预下载的 tarball 命名不完全匹配
- 日志截断导致真正的错误信息未出现在提供的片段中（如 cmake 配置错误、configure 错误、编译错误等）

## 修复方向

### 方向 1（置信度: 中）
检查 libaio 在 openEuler 24.03-lts-sp3 + GCC 12.3.1 环境下的编译是否正常。如果 libaio 需要特定构建依赖（如 `libtool` 已安装但可能还需要 `autoconf automake` 等），在 `dnf install` 中补充。可以通过单独运行 libaio 的编译来验证。

### 方向 2（置信度: 低）
如果 libaio 源码与当前编译器/环境不兼容，考虑用 `dnf install libaio-devel` 系统包替代源码编译，并在 getdeps 调用中通过 `--allow-system-packages` 或其 manifest 文件让 getdeps 使用系统已安装的 libaio。

## 需要进一步确认的点
1. **libaio 构建的实际错误信息**：当前日志在 `Assessing libaio...` 处截断，需要获取完整的 Docker build 日志（特别是 libaio 评估/构建阶段的输出）以确定具体错误原因（如 cmake/configure/编译错误）。
2. **libaio 在 openEuler 上的编译兼容性**：确认 `libaio-0.3.113` 源码在 GCC 12.3.1 下是否能正常编译，是否需要额外的 autotools 或其他构建工具。
3. **getdeps 的 libaio manifest**：查看 fbthrift 源码中 `build/fbcode_builder/manifests/libaio` 的定义，确认其对下载文件名、构建命令的期望是否与预下载的 tarball 匹配。

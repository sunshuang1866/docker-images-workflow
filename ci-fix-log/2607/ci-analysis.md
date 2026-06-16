# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: fbthrift libaio 构建失败
- 新模式症状关键词: Assessing libaio, exit code: 1, fbthrift, getdeps, cmake

## 根因分析

### 直接错误
```
#11 336.2 Building googletest...
#11 336.2 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
> [5/5] RUN git clone -b v2026.06.15.00 --depth 1 https://github.com/facebook/fbthrift.git /build && ...
------
Dockerfile:18
```

### 根因定位
- 失败位置: Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile:18
- 失败原因: fbthrift 的 getdeps 构建系统在处理 libaio 依赖时出错（exit code 1），具体错误信息未在截断日志中显示。之前的依赖项（ninja、zstd、zlib、fmt、boost、fast_float、gflags、glog、googletest）均构建成功，唯独 libaio 在 `Assessing` 阶段失败。

### 与 PR 变更的关联
PR 变更是**完全新增**的 Dockerfile 和相关文件（fix_getdeps.py、libaio tarball），并非对已有构建的修改。上一次成功的 fbthrift 版本是 2026.05.18.00。本次升级到 2026.06.15.00 后，上游 fbthrift 的 getdeps 构建系统或 libaio 依赖清单可能发生了变更，导致以下可能之一：
1. fix_getdeps.py 的 patch 逻辑对新版 fbthrift 源码不完全适用（如 patch 的字符串匹配失败但未被检测到）
2. libaio 的 cmake 构建在 openEuler 24.03-lts-sp3 环境下缺少必要的编译依赖
3. 预下载的 libaio tarball（libaio-libaio-0.3.113.tar.gz）与 getdeps 期望的命名/结构不一致

## 修复方向

### 方向 1（置信度: 中）
检查日志中"Assessing libaio..."之后的详细构建输出（当前日志被截断），确认 libaio 构建失败的具体原因。常见可能是 cmake 缺少对 libaio 的构建配置、或 openEuler 缺少 libaio 编译所需的系统库（如 `libaio-devel`）。如果是系统库缺失，在 Dockerfile 的 `dnf install` 步骤中补充相应包。

### 方向 2（置信度: 低）
检查 fbthrift 上游 v2026.06.15.00 版本中 `build/fbcode_builder/getdeps/getdeps_platform.py` 和 `build/fbcode_builder/getdeps/fetcher.py` 的源码是否发生了变化，确认 fix_getdeps.py 中的字符串匹配和正则替换仍能正确生效。如果上游文件结构或代码格式变更导致 patch 静默失效，需要调整 fix_getdeps.py 的匹配逻辑。

### 方向 3（置信度: 低）
确认预下载的 libaio tarball 是否与 openEuler 24.03-lts-sp3 的编译器/工具链兼容。如果 libaio 0.3.113 版本本身在该环境下无法编译，需要升级 tarball 版本或增加适配补丁。

## 需要进一步确认的点
1. **libaio 构建的具体错误信息**：当前 CI 日志在 "Assessing libaio..." 后即截断，未显示 libaio cmake 或编译阶段的实际报错。需要获取完整日志（包括 `cmake --build` 输出的 stderr）才能精确定位。
2. **upstream fbthrift v2026.06.15.00 的 getdeps 源码变动**：需对比 v2026.05.18.00 → v2026.06.15.00 版本间 `getdeps_platform.py` 和 `fetcher.py` 的 diff，确认 fix_getdeps.py 的 patch 仍然有效。
3. **libaio 在 openEuler 上的系统包可用性**：确认 `dnf` 仓库中是否有 `libaio-devel`，以及 `--allow-system-packages` 标志是否可能跳过本地 tarball 转而使用系统包（但系统包不存在）。

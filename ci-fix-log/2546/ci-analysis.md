# CI 失败分析报告

## 基本信息
- PR: #2546 — 【自动升级】libyuv容器镜像升级至1948版本
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: NEON符号缺失链失败
- 新模式症状关键词: undefined reference, RGBToUVMatrixRow_NEON, collect2: error, ld returned 1 exit status, aarch64

## 根因分析

### 直接错误
```
#8 5.360 /usr/bin/ld: libyuv.a(convert.cc.o): in function `RGB24ToI420':
#8 5.360 convert.cc:(.text+0x4dd0): undefined reference to `RGBToUVMatrixRow_NEON'
#8 5.360 /usr/bin/ld: convert.cc:(.text+0x4dd4): undefined reference to `RGBToUVMatrixRow_NEON'
#8 5.360 /usr/bin/ld: libyuv.a(convert.cc.o): in function `RAWToI420':
#8 5.360 convert.cc:(.text+0x539c): undefined reference to `RGBToUVMatrixRow_NEON'
#8 5.360 /usr/bin/ld: convert.cc:(.text+0x53a0): undefined reference to `RGBToUVMatrixRow_NEON'
#8 5.361 /usr/bin/ld: libyuv.a(row_any.cc.o): in function `RGBToUVMatrixRow_Any_NEON':
#8 5.361 row_any.cc:(.text+0x89ac): undefined reference to `RGBToUVMatrixRow_NEON'
#8 5.361 /usr/bin/ld: libyuv.a(row_any.cc.o):row_any.cc:(.text+0x8b14): more undefined references to `RGBToUVMatrixRow_NEON' follow
#8 5.368 collect2: error: ld returned 1 exit status
#8 5.370 make[2]: *** [CMakeFiles/yuvconvert.dir/build.make:98: yuvconvert] Error 1
#8 5.371 make[1]: *** [CMakeFiles/Makefile2:287: CMakeFiles/yuvconvert.dir/all] Error 2
#8 5.371 make: *** [Makefile:156: all] Error 2
```

### 根因定位
- 失败位置: aarch64 架构构建（日志中安装的包均为 `.aarch64`），链接 `yuvconvert` 可执行文件时
- 失败原因: libyuv 1948 源码中，函数 `RGBToUVMatrixRow_NEON` 被 `convert.cc` 和 `row_any.cc` 调用，但其实现所在的源文件未被纳入 `yuv_common_objects` 或链接目标的编译/链接范围内，导致 aarch64 平台上产生未定义符号链接错误。日志显示 `yuv_neon64` 目标已成功编译（包含 `row_neon64.cc`、`rotate_neon64.cc`、`compare_neon64.cc`、`scale_neon64.cc`），但 `RGBToUVMatrixRow_NEON` 的定义不在这些已编译文件中，说明 libyuv 1948 的 CMakeLists.txt 存在上游缺陷——某个 NEON 实现的源文件未被正确添加到构建目标中。

### 与 PR 变更的关联
PR 变更仅为新增 libyuv 1948 版本的 Dockerfile、README 条目、image-info.yml 条目和 meta.yml 条目，**未修改任何构建逻辑**。失败原因是 libyuv 1948 上游源码在 aarch64 平台的 CMake 配置缺陷——`RGBToUVMatrixRow_NEON` 函数声明与定义分离，定义所在的源文件未被 CMakeLists.txt 包含。此失败与 PR 代码变更无直接关联，但 PR 引入了该版本镜像，因此触发了此问题。

注：日志末尾的 `UndefinedVar: Usage of undefined variable '$LD_LIBRARY_PATH' (line 19)` 是 Dockerfile 中 `ENV LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 自引用产生的 BuildKit 警告，**不是**构建失败的直接原因，仅为次要问题。

## 修复方向

### 方向 1（置信度: 中）
上游 libyuv 1948 的 CMakeLists.txt 中 `RGBToUVMatrixRow_NEON` 的实现文件未被包含在 aarch64 构建目标中。需要在 Dockerfile 的 `git clone` 之后、`cmake` 之前，通过 `sed` 或 patch 向 CMakeLists.txt 补充缺失的源文件，或检查 libyuv 上游 issue 看是否有官方修复/补丁可应用。

### 方向 2（置信度: 低）
参考历史同类问题（如已有的 libyuv 1934、1922 等版本 Dockerfile），检查其是否使用了额外的 cmake 参数或有特殊构建步骤（如禁用 `yuvconvert` 目标或单独编译某 NEON 源文件），将已验证可用的构建方式应用于此新版本。

## 需要进一步确认的点
1. 对比 libyuv 1934（已验证通过）和 libyuv 1948 的 CMakeLists.txt，确认 `RGBToUVMatrixRow_NEON` 定义所在的源文件在两个版本间的增删变化，以及为何 1948 版本缺失该实现
2. 确认日志中的 Docker BuildKit `UndefinedVar` 警告是否导致部分 step 被跳过（虽然可能性较低，但在严格模式下 `ENV` 引用未定义变量理论上可能导致构建中止）
3. 确认是否需要将 `ENV LD_LIBRARY_PATH` 这行移到 `RUN git clone...` 之前或使用 `${LD_LIBRARY_PATH:-}` 默认值语法来消除警告

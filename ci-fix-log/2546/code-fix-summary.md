# 修复摘要

## 修复的问题
libyuv 1948 在 aarch64 平台构建时，`RGBToUVMatrixRow_NEON` 函数实现缺失导致链接失败（undefined reference）。

## 修改的文件
- `Others/libyuv/1948/24.03-lts-sp3/Dockerfile`: 添加 sed 命令注释掉 row.h 中缺失实现的宏定义，修复 ENV LD_LIBRARY_PATH 自引用警告

## 修复逻辑
1. **NEON 符号缺失**：libyuv 1948 上游源码中，`row.h` 第 602 行（aarch64 条件块内）定义了 `HAS_RGBTOUVMATRIXROW_NEON`，但 `RGBToUVMatrixRow_NEON` 函数的实际实现未存在于任何源文件中（`row_neon64.cc` 和 `row_neon.cc` 中均只有 `ARGBToUVMatrixRow_NEON`，缺少不带 A 前缀的 `RGBToUVMatrixRow_NEON`）。这导致 aarch64 链接时 `convert.cc` 和 `row_any.cc` 引用该函数产生未定义符号错误。修复方案是在 `git clone` 之后、`cmake` 之前通过 `sed` 将此 `#define` 注释掉，使编译器回退到 C 语言实现。

2. **ENV 警告**：`ENV LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 在 Docker BuildKit 中会产生 "UndefinedVar" 警告（首次定义时变量尚未存在）。改为 `${LD_LIBRARY_PATH:-}` 使用 bash 默认值语法消除警告。

## 潜在风险
- 在 aarch64 平台上，`RGBToUVMatrixRow` 将使用 C 语言通用实现而非 NEON 优化实现，性能有所下降，但功能正常。其他架构（x86_64、32-bit ARM）不受影响。
- 如果后续 libyuv 版本修复了该缺失实现，此 workaround 需移除。
# 修复摘要

## 修复的问题
Dockerfile 中 `ENV LD_LIBRARY_PATH` 自引用了未定义变量 `$LD_LIBRARY_PATH`，导致 BuildKit 产生 `UndefinedVar` 警告。

## 修改的文件
- `Others/libyuv/1948/24.03-lts-sp3/Dockerfile`: 移除第 19 行 `ENV` 指令中末尾的 `:$LD_LIBRARY_PATH`，仅保留绝对路径赋值。

## 修复逻辑
原指令 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 在一个全新的构建阶段中引用了 `$LD_LIBRARY_PATH`，但该变量此前从未被定义，BuildKit 检测到对未定义变量的引用并产生警告。由于基础镜像中无需追加系统已有路径，直接赋值为 `/usr/local/lib:/libyuv/build` 即可，无需自引用。

## 潜在风险
无。`$LD_LIBRARY_PATH` 在当前构建阶段中未定义，移除其引用后不会改变实际运行时的库搜索路径行为。
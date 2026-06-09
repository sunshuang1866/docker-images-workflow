# 修复摘要

## 修复的问题
Dockerfile 第 19 行 `ENV LD_LIBRARY_PATH` 自引用了未定义的 `$LD_LIBRARY_PATH` 变量，触发 BuildKit `UndefinedVar` 警告。

## 修改的文件
- `Others/libyuv/1948/24.03-lts-sp3/Dockerfile`: 将第 19 行 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib:/libyuv/build`，移除对未定义变量的自引用。

## 修复逻辑
在一个全新的 `FROM` 构建阶段中，`$LD_LIBRARY_PATH` 未被此前任何指令定义，因此在 `ENV` 中拼接引用它是一个未定义变量。由于基础镜像 `openeuler/openeuler:24.03-lts-sp3` 是轻量基础镜像，未预置 `LD_LIBRARY_PATH`，该自引用既无效也无必要。移除后，所需的库路径 `/usr/local/lib` 和 `/libyuv/build` 仍被正确设置。

## 潜在风险
无。移除的自引用部分原本就解析为空值，实际 `LD_LIBRARY_PATH` 值行为不变。
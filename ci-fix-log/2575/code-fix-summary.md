# 修复摘要

## 修复的问题
Ceph cmake 配置阶段找不到 `grpc_cpp_plugin` 可执行文件导致构建失败，同时修复 ENV 自引用未定义变量的 BuildKit 警告。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 
  - 在 `dnf install` 依赖列表中添加 `grpc-plugins` 包（第 24 行），提供 `grpc_cpp_plugin` 二进制文件
  - 将 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 改为 `ENV LD_LIBRARY_PATH=/usr/local/lib64:${LD_LIBRARY_PATH:-}`（第 48 行），消除 UndefinedVar 警告

## 修复逻辑
1. **构建失败根因**：分析报告指出 Ceph 编译的 cmake 配置阶段缺少 `grpc_cpp_plugin`（gRPC 代码生成编译器插件）。虽然 `grpc++` 库被自动安装，但插件二进制文件位于独立的 `grpc-plugins` 包中，未被显式声明。在 `dnf install` 中添加 `grpc-plugins` 即可提供该工具。
2. **非致命警告修复**：`ENV` 指令中使用 `$LD_LIBRARY_PATH` 引用了自身，在首次设置时该变量未定义，BuildKit 会报告 UndefinedVar 警告。使用 `${LD_LIBRARY_PATH:-}` 语法（bash 默认值扩展）可消除此警告。

## 潜在风险
无。`grpc-plugins` 是 `grpc_cpp_plugin` 的标准提供包，不会引入不兼容的依赖或影响其他包。`${LD_LIBRARY_PATH:-}` 语法与 `$LD_LIBRARY_PATH` 在变量已设置时行为完全一致，仅在变量未定义时提供空字符串作为默认值。
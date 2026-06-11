# 修复摘要

## 修复的问题
Ceph cmake 构建阶段找不到 `grpc_cpp_plugin` 编译器插件，因 Dockerfile 的 `dnf install` 缺少 `grpc-plugins` 包。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 包列表末尾添加 `grpc-plugins`

## 修复逻辑
CI 失败根因是 Dockerfile 第 42 行 `./do_cmake.sh` 执行时，cmake 配置脚本检测到 gRPC 1.60.0 存在后尝试查找 `grpc_cpp_plugin` 可执行文件，但 `dnf install` 步骤未安装提供该插件的 `grpc-plugins` 包。在包列表中补充 `grpc-plugins` 后，cmake 配置阶段应能顺利找到该插件并完成构建。

## 潜在风险
无。`grpc-plugins` 是标准 openEuler 仓库提供的包，与已有依赖无冲突。
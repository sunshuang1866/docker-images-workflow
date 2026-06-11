# 修复摘要

## 修复的问题
Dockerfile 缺少 `protobuf-devel` 和 `protobuf-compiler` 编译依赖，导致 Ceph CMake 配置阶段失败（`Could NOT find Protobuf`）。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 三处修改：(1) 修复 `FROM ... as` → `FROM ... AS` 关键字大小写；(2) 在 `dnf install` 中补充 `protobuf-devel protobuf-compiler`；(3) 修复 `$LD_LIBRARY_PATH` 自引用为 `${LD_LIBRARY_PATH:-}`。

## 修复逻辑
CI 分析报告指出根因是 Ceph 21.3.0 的 CMake 构建调用了 `find_package(Protobuf)`，但系统未安装 protobuf 开发包。修复通过在 `dnf install` 命令中补充 `protobuf-devel` 和 `protobuf-compiler` 解决。同时修复了 BuildKit 报告的两个非致命警告（`as` 大小写和 `LD_LIBRARY_PATH` 未定义自引用），避免潜在问题。

## 潜在风险
无。补充 protobuf 开发包是 Ceph 21.3.0 版本的硬性编译依赖，不影响其他版本或其他组件。两个警告修复均为纯语法修正，不改变行为。
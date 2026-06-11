# 修复摘要

## 修复的问题
Ceph 21.3.0 镜像构建时 cmake 配置阶段找不到 Protobuf 库和头文件，导致构建失败；同时修复 LD_LIBRARY_PATH 自引用未定义变量的 BuildKit 警告。

## 修改的文件
- `Storage/ceph/21.3.0/24.03-lts-sp3/Dockerfile`: 在 dnf install 步骤中添加 `protobuf protobuf-devel` 包；将 `ENV LD_LIBRARY_PATH` 中的 `$LD_LIBRARY_PATH` 改为 `${LD_LIBRARY_PATH:-}`

## 修复逻辑
1. **protobuf 缺失（根因）**：ceph 源码 `src/CMakeLists.txt:1029` 调用 `find_package(Protobuf)` 需要 `Protobuf_LIBRARIES` 和 `Protobuf_INCLUDE_DIR`，这些由 `protobuf-devel` 提供。Dockerfile 的 dnf install 遗漏了此依赖，导致 cmake 配置失败。修复方式为在 dnf install 的包列表中添加 `protobuf protobuf-devel`。
2. **LD_LIBRARY_PATH 警告（预防性修复）**：原 `ENV LD_LIBRARY_PATH=/usr/local/lib64:$LD_LIBRARY_PATH` 在首次设置该变量时引用了自身，产生 BuildKit 未定义变量警告。使用 `${LD_LIBRARY_PATH:-}` 替代，当变量未定义时展开为空字符串，消除警告。

## 潜在风险
无。protobuf 和 protobuf-devel 是 Ceph 构建的标准依赖，ceph 源码的 cmake 脚本明确声明了此需求；LD_LIBRARY_PATH 的修改仅改变 shell 变量展开行为，不影响运行时的库搜索路径逻辑。
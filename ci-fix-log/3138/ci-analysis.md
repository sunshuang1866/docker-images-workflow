# CI 失败分析报告

## 基本信息
- PR: #3138 — chore(onnxruntime): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包名不可用
- 新模式症状关键词: Unable to find a match, yum install, gcc-toolset-14-c++*, No match for argument

## 根因分析

### 直接错误
```
#7 21.83 No match for argument: gcc-toolset-14-c++*
#7 21.85 Error: Unable to find a match: gcc-toolset-14-c++*
#7 ERROR: process "/bin/sh -c yum update -y &&     yum install -y         tar         ca-certificates         gcc-toolset-14-gcc*         gcc-toolset-14-binutils*         gcc-toolset-14-c++*         python3-devel         python3-pip         python3-setuptools         python3-wheel         python3-numpy         python3-flatbuffers         python3-packaging         python3-protobuf         git &&     yum clean all &&     rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `AI/onnxruntime/1.22.1/24.03-lts-sp4/Dockerfile:14`（yum install 行中 `gcc-toolset-14-c++*` 包名）
- 失败原因: openEuler 24.03-LTS-SP4 仓库中不存在名为 `gcc-toolset-14-c++*` 的 RPM 包，yum 无法匹配到任何包导致安装失败。注意 `gcc-toolset-14-gcc*` 和 `gcc-toolset-14-binutils*` 未报错（日志仅报 c++ 包缺失），说明 gcc-toolset-14 工具集在 SP4 中可用的包名结构可能与 SP2 不同，C++ 相关包可能已合并到 gcc 包中，或使用了不同的命名（如 `gcc-toolset-14-gcc-c++*`、`gcc-toolset-14-libstdc++-devel*` 等）。

### 与 PR 变更的关联
PR 新增了 `AI/onnxruntime/1.22.1/24.03-lts-sp4/Dockerfile`，其中 `yum install` 步骤直接引用了在 openEuler 24.03-LTS-SP4 仓库中不存在的包名 `gcc-toolset-14-c++*`。该失败由本次 PR 改动直接引入。

## 修复方向

### 方向 1（置信度: 中）
确认 openEuler 24.03-LTS-SP4 中 gcc-toolset-14 实际提供的 C++ 相关包名。常见可能性：
- C++ 编译器已包含在 `gcc-toolset-14-gcc*` 内，`gcc-toolset-14-c++*` 本身多余，直接删除该行即可
- 包名格式为 `gcc-toolset-14-gcc-c++*`（带 `gcc-` 前缀），将 Dockerfile 中 `gcc-toolset-14-c++*` 改为 `gcc-toolset-14-gcc-c++*`

### 方向 2（置信度: 低）
如果 SP4 的 gcc-toolset-14 包结构与 SP2 完全不同，可能需要参照已有的 SP2 Dockerfile 并对比 SP4 仓库中实际可用的 gcc-toolset-14 子包列表，重新整理 yum install 的包清单。

## 需要进一步确认的点
1. 在 openEuler 24.03-LTS-SP4 容器中运行 `yum search gcc-toolset-14` 或 `yum list available | grep gcc-toolset-14`，确认实际可用的 gcc-toolset-14 子包名称列表，特别是 C++ 编译器对应的包名
2. 确认 `gcc-toolset-14-gcc*` 是否已经包含了 C++ 编译器（即 `g++`），若已包含则 `gcc-toolset-14-c++*` 行可直接移除
3. 可参考已通过 CI 的同项目 SP2 版本 Dockerfile（`AI/onnxruntime/1.22.1/24.03-lts-sp2/Dockerfile`），对比 SP2 与 SP4 在 gcc-toolset-14 包名上的差异

## 修复验证要求
修复后需在 openEuler 24.03-LTS-SP4 容器环境中验证 `yum install` 命令可成功执行，确保所有列出的包名均能匹配到实际 RPM 包。

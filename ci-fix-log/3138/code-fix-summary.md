# 修复摘要

## 修复的问题
移除 openEuler 24.03-LTS-SP4 中不存在的 `gcc-toolset-14-c++*` 包安装行，修复 yum install 失败。

## 修改的文件
- `AI/onnxruntime/1.22.1/24.03-lts-sp4/Dockerfile`: 删除了第 14 行的 `gcc-toolset-14-c++* \`

## 修复逻辑
在 openEuler 24.03-LTS-SP4 中，`gcc-toolset-14-c++*` 包不存在。但该包提供的 C++ 编译器（gcc-c++）已通过同文件第 12 行的 `gcc-toolset-14-gcc*` 通配符安装。yum 的 glob 匹配中，`gcc-toolset-14-gcc*` 会匹配所有以该前缀开头的子包，包括 `gcc-toolset-14-gcc-c++`（C++ 编译器包）。因此 `gcc-toolset-14-c++*` 行在 SP4 中既是多余的，又引用了不存在的包名，直接删除即可。

## 潜在风险
无。`gcc-toolset-14-gcc*` 通配符已能覆盖 C++ 编译器的安装，删除该行不影响编译功能。
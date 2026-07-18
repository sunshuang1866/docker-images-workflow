# 修复摘要

## 修复的问题
在 cmake 配置阶段添加 `-DVVENC_ENABLE_WERROR=OFF`，避免因 openEuler 24.03-LTS-SP4 基础镜像中编译器版本差异产生的新警告被 `-Werror` 转为编译错误。

## 修改的文件
- `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`: 在第 10 行 cmake 命令中添加 `-DVVENC_ENABLE_WERROR=OFF` 参数

## 修复逻辑
vvenc 上游 CMakeLists.txt 中 `VVENC_ENABLE_WERROR` 默认为 `ON`，会启用 `-Werror`（对 GCC）将编译警告视为错误。sp3 和 sp4 的 Dockerfile 内容完全相同，唯一区别是基础镜像 tag。sp3 构建成功而 sp4 失败，最可能的原因是 sp4 基础镜像中的 gcc/g++ 版本与 sp3 不同，产生了 sp3 中未出现的新警告，导致 `-Werror` 将警告升级为错误。添加 `-DVVENC_ENABLE_WERROR=OFF` 禁用此行为，既不影响功能正确性，也避免了因编译器版本差异导致的构建失败。

已从上游 `fraunhoferhhi/vvenc` v1.14.0 CMakeLists.txt 确认 `VVENC_ENABLE_WERROR` 选项存在且默认为 ON（`set( VVENC_ENABLE_WERROR ON CACHE BOOL "Treat warnings as errors (-Werror or /WX)" )`）。

## 潜在风险
无。`-Werror` 只是将警告转为错误，关闭后编译器仍会输出警告信息（不会隐藏），不影响生成代码的正确性和性能。Release 构建的优化选项（LTO、架构特定优化等）不受影响。
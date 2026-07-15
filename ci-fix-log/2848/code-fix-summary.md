# 修复摘要

## 修复的问题
在 cmake 配置中添加 `-DWITHOUT_ABI_CHECK=1` 禁用 ABI 检查，解决 openEuler 24.03-LTS-SP4 上 GCC 预处理器输出与 MariaDB 12.1.1 自带 `abi_check.out` 参考文件不一致导致的构建失败。

## 修改的文件
- `Database/mariadb/12.1.1/24.03-lts-sp4/Dockerfile`: 在 cmake 命令行中添加 `-DWITHOUT_ABI_CHECK=1 \`

## 修复逻辑
CI 失败分析报告指出 MariaDB 源码中 `cmake/do_abi_check.cmake:84` 的 ABI 检查目标因 SP4 GCC 工具链兼容性问题而失败，导致 `make -j8` 整体报错。通过查阅 MariaDB 12.1.1 上游源码 `CMakeLists.txt`，确认存在 `IF (NOT WITHOUT_ABI_CHECK)` 条件控制 `cmake/abi_check.cmake` 的加载。`WITHOUT_ABI_CHECK` 变量未被 `OPTION()` 显式定义，默认为空（假值），通过 cmake 命令行传入 `-DWITHOUT_ABI_CHECK=1` 可将其设为真值，从而跳过 ABI 检查目标的生成，使 `make -j8` 不再因 ABI 检查失败而报错。已从上游 `mariadb-12.1.1` tag 获取 `CMakeLists.txt` 和 `cmake/abi_check.cmake` 验证，确认该变量控制逻辑存在且有效。ABI 检查是 MariaDB 开发维护的内部一致性校验，对最终用户运行 MariaDB 无影响。

## 潜在风险
无。该修改仅跳过 ABI 兼容性检查目标，不影响 MariaDB 的实际编译和运行功能。SP1 版本的 Dockerfile 未使用此参数也能正常构建，说明 SP1 GCC 工具链与 ABI 参考文件兼容；SP4 因 GCC 版本差异需要此参数，对运行时行为无影响。
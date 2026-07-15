# CI 失败分析报告

## 基本信息
- PR: #2848 — chore(mariadb): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: MariaDB ABI 检查工具链不兼容
- 新模式症状关键词: ABI check found difference, do_abi_check.cmake, plugin_audit.h.pp, Check size of uint32 - failed

## 根因分析

### 直接错误
```
#8 74.95 CMake Error at cmake/do_abi_check.cmake:84 (MESSAGE):
#8 74.95   ABI check found difference between /mariadb/abi_check.out and
#8 74.95   /mariadb/include/mysql/plugin_audit.h.pp
#8 74.95 
#8 74.95 make[2]: *** [CMakeFiles/abi_check.dir/build.make:70: CMakeFiles/abi_check] Error 1
#8 74.96 make[1]: *** [CMakeFiles/Makefile2:3823: CMakeFiles/abi_check.dir/all] Error 2
#8 78.91 make: *** [Makefile:166: all] Error 2
```

### 根因定位
- 失败位置: MariaDB 源码内 `cmake/do_abi_check.cmake:84`（abi_check 构建目标）
- 失败原因: openEuler 24.03-LTS-SP4 上的 GCC 预处理器输出与 MariaDB 12.1.1 源码自带的 `abi_check.out` 参考文件不一致，ABI 检查目标构建失败，进而导致 `make -j8` 整体返回错误码 2。

### 症状背景
cmake 配置阶段出现大量基础类型检测失败（`Check size of uint32 - failed`、`Check size of int64 - failed`、`Check size of socklen_t - failed` 等），表明 openEuler 24.03-LTS-SP4 上的 GCC 工具链在执行 cmake `try_compile()` 测试程序时存在兼容性问题。尽管配置阶段检测到的部分特性失败，cmake 仍成功生成构建文件，且实际编译步骤（wsrep_api、zlib、readline、tpool 等目标）能正常编译通过。**ABI 检查目标**在构建早期（0%）即失败，`make -j8` 并行构建中其他目标继续编译至完成，但最终因 ABI 检查失败而整体报错。

### 与 PR 变更的关联
PR 变更引入的是一个**全新 Dockerfile**（`Database/mariadb/12.1.1/24.03-lts-sp4/Dockerfile`），该 Dockerfile 在 openEuler 24.03-LTS-SP4 基础镜像上编译 MariaDB 12.1.1。同版本的 SP1 变体（`12.1.1/24.03-lts-sp1/`）在 PR 中未被修改，说明该问题特属于 SP4 平台的工具链。Dockerfile 本身没有语法或逻辑错误——这是 MariaDB 上游 ABI 检查机制与 SP4 平台 GCC 版本的兼容性问题。

## 修复方向

### 方向 1（置信度: 高）
在 cmake 配置中禁用 ABI 检查。ABI 检查是 MariaDB 开发维护的内部一致性校验，它对最终用户运行 MariaDB 无影响。在 cmake 命令行中添加参数禁用该检查目标，例如 `-DWITH_ABI_CHECK=OFF` 或类似选项。需要确认 MariaDB 12.1.1 的 cmake 是否支持此类选项（查阅 `cmake/do_abi_check.cmake` 及顶层 `CMakeLists.txt`）。

### 方向 2（置信度: 中）
跳过 `abi_check` 构建目标。如果 MariaDB 12.1.1 没有提供禁用 ABI 检查的 cmake 开关，可在 `make` 命令中显式指定要构建的目标，排除 `abi_check`（例如使用 `make -j8 mariadb` 代替 `make -j8 all`）。需要查阅 MariaDB 12.1.1 的顶层 `Makefile` 确认正确的可用构建目标名称。

## 需要进一步确认的点
1. MariaDB 12.1.1 源码中 `cmake/do_abi_check.cmake:84` 的具体逻辑——ABI 检查是否可通过 cmake 参数关闭
2. MariaDB 12.1.1 的 cmake 选项列表——是否存在 `WITH_ABI_CHECK` 或类似的开关
3. SP1 版本的 MariaDB 12.1.1 Dockerfile（`12.1.1/24.03-lts-sp1/Dockerfile`）是否有针对 ABI 检查的特殊处理，可作为参考
4. openEuler 24.03-LTS-SP4 与 SP1 的 GCC 版本差异，以确认工具链变化是根本原因

## 修复验证要求
若修复方向 1 涉及 cmake 参数变更，code-fixer 需确认 MariaDB 12.1.1 源码确实支持该参数：
- 下载 `https://archive.mariadb.org/mariadb-12.1.1/source/mariadb-12.1.1.tar.gz`
- 查阅 `cmake/do_abi_check.cmake` 和顶层 `CMakeLists.txt` 中与 ABI 检查相关的选项定义
- 若方向 1 不可行（无禁用开关），再尝试方向 2，验证 `make` 目标名称是否正确

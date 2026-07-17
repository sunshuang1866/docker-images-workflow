# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```
完整上下文（CI phases 时间线）：
```
2026-07-09 09:40:23,529 - INFO - [Build] finished
2026-07-09 09:40:23,529 - INFO - [Push] finished
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 宿主机的测试框架脚本）
- 失败原因: CI [Check] 阶段在执行容器验证测试时，`common_funs.sh` 第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但该依赖在 CI 测试运行环境中未安装或不在 `PATH` 中，导致整个 Check 阶段在初始化测试框架时即崩溃。

### 与 PR 变更的关联
PR 变更内容为新增 PostgreSQL 17.6 on openEuler 24.03-LTS-SP4 的 Dockerfile 和 entrypoint.sh，以及对应的 meta.yml 和 README 条目。Docker 镜像构建和推送阶段均已完成且成功（`#8 DONE 268.4s`，`#11 DONE 58.0s`，`[Build] finished`，`[Push] finished`）。失败发生在构建完成之后的 **eulerpublisher CI 工具 [Check] 阶段**，属于 CI 测试基础设施自身的依赖缺失问题，与 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
在 CI 测试运行环境中安装 `shunit2`。`shunit2` 是一个 Shell 单元测试框架，通常通过包管理器（如 `dnf install shunit2` 或 `apt install shunit2`）安装，也可从 GitHub (`kward/shunit2`) 下载后放到 `/usr/local/bin/` 下。确认 CI 测试节点的 `PATH` 中包含 `shunit2` 可执行文件的位置。

### 方向 2（置信度: 低）
如果其他同类 PR 在同一 CI 环境中 Check 阶段能正常通过，则可能是本次 CI 运行使用的 runner 节点环境异常（如镜像未正确安装 shunit2）。可尝试重新触发 CI 运行，观察是否仍复现。

## 需要进一步确认的点
1. CI 测试节点的标准软件清单中是否应包含 `shunit2`？同一 CI 环境下其他 PR 的 Check 阶段是否正常通过？
2. `common_funs.sh` 第 13 行引用 `shunit2` 的具体方式（是通过 source、绝对路径还是 PATH 查找），以确定正确的修复方向。
3. entrypoint.sh 中 `arch=` 行（第 4 行）的 `case` 语法在 Bash 命令替换 `$()` 内是否完全兼容，建议在修复 CI infra 问题后对此进行独立验证，防止 Check 阶段恢复正常后暴露出容器启动阶段的问题。

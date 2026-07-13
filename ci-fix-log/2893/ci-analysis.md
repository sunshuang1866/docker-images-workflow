# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 环境中缺少 `shunit2`（Shell 单元测试框架）包，`common_funs.sh` 第 13 行执行 `. shunit2`（source 加载）时找不到该文件，导致 `[Check]` 阶段的容器启动测试无法执行。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置，以及更新 README、image-info.yml、meta.yml 等元数据文件。日志显示所有构建阶段（meson 编译 422/422 通过、docker build 成功、镜像 push 成功）均正常完成，失败仅发生在 CI 测试框架层（`[Check]` 阶段）因 runner 环境缺少 `shunit2` 依赖导致测试脚本无法运行。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包。openEuler 中可直接通过 `yum install shunit2` 安装，或从 `https://github.com/kward/shunit2` 获取并配置到 `PATH` 中。此问题与本次 PR 代码无关，属 CI 基础设施配置问题。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装在 runner 上但路径未正确配置，检查 `common_funs.sh` 中 source 路径（如 `PATH`、`SHUNIT2_HOME` 环境变量）是否正确指向 `shunit2` 的安装位置。

## 需要进一步确认的点
1. 确认 CI runner 上是否已安装 `shunit2` 包以及安装路径
2. 确认该 runner 上其他同类 PR 的 `[Check]` 阶段是否也出现相同错误（判断是单次环境故障还是系统性缺少依赖）
3. 确认是否存在 x86-64（amd64）架构的独立构建 job 未在提供的日志中——当前日志仅展示 aarch64 架构的构建+测试流程，amd64 的结果未知

## 修复验证要求
无需验证 PR 代码变更。修复方向为 CI 基础设施层面（安装 `shunit2`），与代码改动无关。Code Fixer 无需处理。

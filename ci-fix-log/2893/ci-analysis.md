# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
- 失败原因: CI 的 [Check] 阶段（镜像构建后的容器启动验证）依赖 `shunit2` shell 单元测试框架，但当前 CI runner 环境中未安装 `shunit2`，导致 `common_funs.sh` 第 13 行 `. shunit2` source 失败，整个 [Check] 阶段报 CRITICAL 并标记构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 的变更仅限于新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、配置文件和元数据条目，不涉及 CI 基础设施或测试框架的配置。镜像构建（编译 422 个目标、链接、安装）和推送均成功完成，失败仅发生在构建后容器启动验证的 [Check] 阶段，属于 CI 运行环境缺少 `shunit2` 依赖所致。Code Fixer 无需处理。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2`。openEuler 上可通过 `yum install shunit2` 或 `dnf install shunit2` 安装，也可从 GitHub 仓库（kward/shunit2）手动部署到 `common_funs.sh` 期望的路径。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 的包仓库中是否存在、包名是否一致（可能是 `shunit2` 或需从源码安装）。
- 确认是否存在另一架构（amd64）的构建 job 及其日志，以排除该架构也有独立失败的情况。
- 确认该 CI runner 上其他成功通过 [Check] 的镜像是否依赖于同一份 `common_funs.sh`——如果其他镜像的 Check 均通过，则可能是该 runner 近期环境变更导致 `shunit2` 丢失。

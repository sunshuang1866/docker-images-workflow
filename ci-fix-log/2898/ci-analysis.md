# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, line 13, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:49,909 - INFO - [Push] finished
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段执行容器测试时，`common_funs.sh` 脚本第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但 `shunit2` 在 CI Runner 上不存在（未安装或路径不可达），导致测试脚本直接失败。

### 与 PR 变更的关联
**与 PR 变更无关（infra-error）。**

Docker 镜像构建和推送均已成功完成（日志中 `#11 DONE 41.9s`、`[Build] finished`、`[Push] finished` 均正常），Dockerfile 中的 5 个步骤（下载 Go → 时间戳修正 → 清理构建工具 / 设置权限 → WORKDIR → CMD）全部顺利执行完毕。失败仅发生在 CI 的后置 [Check] 阶段，是一个纯 CI 基础设施问题：

1. PR 仅新增了 Go 1.25.6 的 Dockerfile 及配套的 README/image-info.yml/meta.yml 更新，均为标准的镜像注册类变更，不存在任何可能影响 CI 测试框架的修改。
2. 错误来源路径 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 是 CI Runner 宿主文件系统中的 `eulerpublisher` 测试工具链，而非容器镜像内部。`shunit2` 是 eulerpublisher CI 测试框架的运行时依赖，缺失属于 CI 环境配置问题。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 上安装/恢复 `shunit2` 工具。`shunit2` 是 Shell 脚本单元测试框架，通常可通过以下方式之一获取：
- 从系统包管理器安装（如 `yum install shunit2` 或 `dnf install shunit2`）
- 从官网下载并放置到 CI Runner 的 PATH 中

需由 CI 基础设施管理员检查该 Runner 上 `shunit2` 的安装状态和 `PATH` 配置。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装但路径变更，需更新 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 第 13 行中 `shunit2` 的引用路径（如从相对路径改为绝对路径，或调整为适配当前 Runner 环境的路径）。

## 需要进一步确认的点
1. **同一 CI Runner 上其他 PR/镜像的 [Check] 阶段是否也失败？** 如果该 Runner 上的其他 job 也在 [Check] 阶段报 `shunit2: No such file or directory`，则可确认为 Runner 环境问题。
2. **x86_64（amd64）架构的构建 job 日志**：当前提供的日志仅包含 aarch64 架构的构建过程，需要确认 x86_64 job 是否也出现相同错误，以判断问题范围。
3. **`shunit2` 的预期安装路径和版本**：确认 `eulerpublisher` 测试框架对 `shunit2` 的依赖声明（是否应随 `eulerpublisher` 包一同安装，还是需单独部署）。

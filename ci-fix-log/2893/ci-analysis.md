# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 未安装
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行器的 [Check] 阶段依赖 `shunit2` shell 单元测试框架来验证容器启动和行为，但 `shunit2` 未安装在该运行器上，导致测试脚本因 `source` 目标文件不存在而直接失败

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件、README.md 和 meta.yml 的版本条目。Docker 镜像构建（aarch64）和推送均已成功完成（`#13 DONE 36.0s`），失败发生在 CI 基础设施层的容器功能验证阶段，属于纯粹的 CI 环境问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 包，使容器的 [Check] 测试阶段能正常执行。这是 CI 基础设施配置问题，**无需修改 PR 中的任何代码或 Dockerfile**。

### 方向 2（置信度: 低）
如果 `shunit2` 在当前 CI runner 环境中确实无法安装（如系统包仓库不可用），可考虑改用其他 shell 测试框架或跳过对该镜像的容器启动测试。但这需要 CI 团队介入调整流水线配置。

## 需要进一步确认的点
1. **确认 shunit2 是否在所有 CI runner 上都缺失**，还是仅当前 aarch64 runner 的问题。若其他 runner 上 shunit2 可用，则说明此 runner 的镜像/配置存在遗漏。
2. **获取 x86_64 架构的构建日志**。当前日志仅展示了 aarch64 的构建+检查流程，x86_64 架构是否通过了构建和检查尚未可知。若 x86_64 的检查也因 shunit2 缺失而失败，则进一步确认这是全局 CI 基础设施问题。
3. **确认 shunit2 是最近从 runner 镜像中移除的，还是一直缺失**。如果历史上该测试一直跳过（如 shunit2 不存在时静默跳过），需检查 `common_funs.sh` 中是否有缺失的 fallback 逻辑导致原本应跳过的测试变成了硬失败。

# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 的 [Check] 阶段依赖 `shunit2` shell 单元测试框架，但当前 runner 环境中未安装该框架，导致 `common_funs.sh` 中 `source shunit2` 失败，整个 check 流程报错退出。

### 与 PR 变更的关联
**此失败与 PR 变更无关。** Docker 镜像构建阶段（[Build]）和推送阶段（[Push]）均已完成并成功：

1. meson 编译 422 个目标全部成功（`[422/422] Linking target named`）
2. meson install 所有组件安装成功（`#9 DONE 41.4s`）
3. Docker 镜像导出和推送成功（`#13 pushing manifest for docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ... done`）
4. 日志明确记录 `[Build] finished` 和 `[Push] finished`
5. 唯一失败在 [Check] 阶段，且错误定位在 eulerpublisher 测试框架自身的依赖缺失，而非容器运行或功能测试失败

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2` 框架包。在 openEuler 环境中可通过以下方式之一解决：
- `yum install shunit2` 或 `dnf install shunit2`
- 将 `shunit2` 脚本放置到 eulerpublisher 可找到的路径

此修复属于 CI 基础设施层面，Code Fixer 无需对仓库代码做任何修改。

## 需要进一步确认的点

1. 确认当前 aarch64 runner 节点上 `shunit2` 是否已安装（`rpm -qa | grep shunit2` 或 `which shunit2`）
2. 确认 x86-64 架构的 bind9 构建 job 是否同样因 `shunit2` 缺失而失败（当前日志仅展示 aarch64 架构 job）
3. 确认 `common_funs.sh` 中 `shunit2` 的预期路径，可能需要在 eulerpublisher 配置中设置正确的 `SHUNIT2_PATH`

## 修复验证要求
不适用（infra-error，无需修改代码）。

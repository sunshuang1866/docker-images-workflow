# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2`（shell 单元测试框架），导致 eulerpublisher 的 [Check] 测试脚本在 source shunit2 时失败。Docker 镜像构建和推送本身均已成功完成（日志中 `#9 DONE 41.4s`、`[Build] finished`、`[Push] finished`、`#13 DONE 36.0s` 均表明构建+推送阶段正常通过）。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，以及更新 README.md、image-info.yml、meta.yml。Docker 镜像的编译、安装、构建、推送全部成功。失败发生在 CI 自身的测试框架（eulerpublisher 的 [Check] 阶段），因 runner 环境缺少 `shunit2` 库而导致测试脚本无法运行。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，需在 runner 上安装 `shunit2`（可通过 `dnf install shunit2` 或等效方式），或修复 `eulerpublisher` 测试脚本中 `shunit2` 的 source 路径。**Code Fixer 无需处理，非 PR 代码问题。**

## 需要进一步确认的点
- 确认 CI 是否也有 x86_64 架构的构建 job，当前日志仅为 aarch64，若 x86_64 同样失败且为同一原因，可进一步确认是基础设施问题。
- 确认 `shunit2` 是否需要由 CI 管理员安装到 runner 镜像中，还是应作为 `eulerpublisher` 的依赖随包发布。

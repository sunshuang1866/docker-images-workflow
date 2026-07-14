# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
#13 DONE 36.0s                      ← 镜像构建 & 推送成功
euler_builder_20260710_092104 removed
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 环境中的容器镜像 [Check] 校验阶段
- 失败原因: Docker 镜像的构建（meson compile 共 422 个目标）和推送均完全成功，失败发生在构建后的容器校验测试环节。校验脚本 `common_funs.sh` 第 13 行尝试 `source shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在 CI runner 的测试环境中（不在 PATH 中），导致 `[Check] test failed`。

### 与 PR 变更的关联
**与本次 PR 变更无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（新文件）、named.conf（新文件）、README.md 和 image-info.yml 的表格更新，以及 meta.yml 的新条目。这些变更均不涉及 CI 环境配置或测试框架安装。镜像构建本身完全成功（100% 编译通过并成功推送至 registry），失败发生在 CI 的容器校验基础设施层面。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2`。shunit2 是 Shell 脚本单元测试框架，CI 的容器镜像校验流程（`eulerpublisher/container/app/app.py` [Check] 阶段）依赖该框架对构建出的镜像执行验证测试。当前 CI runner 缺少该依赖，导致所有需经 [Check] 阶段校验的镜像构建均可能失败。此问题不是本次 PR 引入的，属于 CI 基础设施配置缺失。

## 需要进一步确认的点
1. 确认 CI runner 镜像/环境中是否本应预装 shunit2，还是因最近的 CI 环境变更导致该依赖丢失。
2. 确认同一 CI runner 上其他 PR 的 [Check] 阶段是否也因相同原因失败，以排除 runner 局部的环境异常。
3. 如果这是该 runner 上首次出现此问题，还需排查 `eulerpublisher` 容器校验框架是否在近期升级后新增了对 shunit2 的依赖。

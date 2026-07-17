# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架缺失 shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI [Check] 阶段在运行容器验证测试时，`common_funs.sh` 脚本尝试 source `shunit2` 测试框架但文件不存在（`shunit2: file not found`）。Docker 镜像的构建（`[Build] finished`）和推送（`[Push] finished`）本身均已成功完成，失败仅发生在 CI 测试框架的依赖缺失上。

### 与 PR 变更的关联
**无关。** PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、命名配置文件及元数据更新。Docker 构建（9个构建阶段全部 DONE，422 个编译目标全部完成、链接、安装均无报错）和镜像推送均成功。`shunit2` 缺失是 CI Runner 环境问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner（`ecs-build-docker-aarch64-*` 节点）上安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试框架，通常通过包管理器（如 `yum install shunit2`）或从源码安装。CI 的 eulerpublisher 工具在 [Check] 阶段依赖它运行容器验证测试，当前 Runner 环境缺少此依赖。

## 需要进一步确认的点
- 确认 CI Runner 节点 `ecs-build-docker-aarch64-*` 上 shunit2 的可用性（是否被误删除或从未安装）
- 确认 shunit2 是否为 openEuler 24.03-LTS-SP4 CI Runner 的标准依赖，是否其他 PR 也遇到了相同问题

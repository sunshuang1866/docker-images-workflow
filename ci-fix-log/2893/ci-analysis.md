# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `Check`, `test failed`

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 后置检查（[Check] 阶段）尝试执行镜像验证测试，但 CI runner 上缺少 `shunit2` 测试框架文件，`common_funs.sh` 在 source 该文件时失败，导致整个 Check 阶段报错退出。

### 与 PR 变更的关联
本次 PR 的代码变更（新增 `Others/bind9/9.21.23/24.03-lts-sp4/Dockerfile`、`named.conf` 及元数据更新）**与 CI 失败无关**。Docker 镜像构建阶段（[Build]）和推送阶段（[Push]）均已成功完成：
- meson 编译全部 422 个目标通过
- 二进制文件安装到镜像各路径正常
- 镜像推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64` 成功

失败发生在构建完成之后、镜像验证测试（[Check]）阶段，根因是 CI runner 环境缺少 `shunit2` 测试框架文件，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装或部署 `shunit2` 测试框架到预期路径（`common_funs.sh` 期望所在路径）。这是 CI 基础设施配置问题，**Code Fixer 无需处理，Dockerfile 和代码无需修改**。

## 需要进一步确认的点
- 确认 `shunit2` 文件在 CI runner 上的预期安装路径，以及为何在当前 runner 上缺失
- 确认其他镜像（如 x86_64 架构）的同版本构建是否也遇到相同的 Check 阶段失败

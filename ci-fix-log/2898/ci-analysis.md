# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 测试阶段在构建完成后验证容器镜像时，`common_funs.sh` 第 13 行尝试引用 `shunit2`（Shell 单元测试框架），但该工具未安装在 CI runner 上，导致测试脚本执行失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相应的 README.md、image-info.yml、meta.yml 元数据条目。Docker 镜像构建（Steps #7-#11）和推送（Push）阶段均已成功完成：
- `#7 DONE 67.8s` — Go 二进制下载解压
- `#8 DONE 40.5s` — 文件时间戳修正与符号链接
- `#9 DONE 1.5s` — 构建工具卸载与清理
- `#11 DONE 41.9s` — 镜像导出与推送（`[Build] finished`, `[Push] finished`）

失败发生在与 PR 代码无关的 CI 后处理阶段——`eulerpublisher` 测试框架因缺少 `shunit2` 依赖而无法执行容器验证测试。

## 修复方向

### 方向 1（置信度: 高）
**在 CI runner 上安装 shunit2**。`shunit2` 是 Shell 脚本单元测试框架，CI 测试脚本 `common_funs.sh` 依赖它来验证构建完成的容器镜像（如启动容器并检查 `go version` 输出）。需在 CI 执行节点的测试环境中安装 `shunit2`（常见安装方式：`dnf install shunit2` 或从 GitHub 获取源码并加入 `PATH`）。

## 需要进一步确认的点
- 确认该 CI runner 节点（aarch64 架构）上是否之前成功运行过其他镜像的 Check 测试——如果同一节点上 SP3 版本 Go 镜像的 Check 测试也曾通过，则 `shunit2` 可能在被本次构建任务触发前被意外移除或环境未正确初始化。
- 确认 `common_funs.sh` 的 `shunit2` 引用是期望 `PATH` 中存在可执行文件，还是期望 `source` 一个脚本文件；据此确定安装/部署方式。

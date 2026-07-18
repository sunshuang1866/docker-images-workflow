# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的 `[Check]` 阶段执行镜像验证测试时，`common_funs.sh` 脚本尝试 source `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在该 CI runner 上。

### 与 PR 变更的关联
**与 PR 无关。** 此次 PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml）。Docker 镜像构建（#7-#11）和推送（Push）均已完成且成功，仅在 CI 流水线的 `[Check]` 后置验证阶段因测试框架工具 `shunit2` 缺失而失败。PR 的代码变更不会影响 CI runner 上是否安装 `shunit2`。

### 日志中"Error lines"说明
日志中 `### Error lines` 区段列出的内容（如 `#7 66.74 go/src/fmt/errors.go`）并非真正的错误信息，而是 Dockerfile 中 `find` 命令遍历 Go 源码目录的输出——这些文件名包含 "error" 字样被日志过滤器误识别为错误行。实际有效的错误仅上述一条 `shunit2: No such file or directory`。

## 修复方向

### 方向 1（置信度: 中）
CI 基础设施团队的运维人员需在 aarch64 架构的 CI runner（`ecs-build-docker-aarch64-*`）上安装 `shunit2` Shell 测试框架。`shunit2` 是一个标准的 Shell 单元测试库，通常可通过以下方式安装：
- 从 EPEL 或类似仓库安装 `shunit2` RPM 包
- 或将 `shunit2` 脚本部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下

该问题属于 CI 基础设施层面，**Code Fixer 无需处理此 PR 的任何文件**。

## 需要进一步确认的点
1. `shunit2` 是仅在 aarch64 runner 上缺失，还是所有架构的 CI runner 上均缺失？需确认其他架构（如 x86_64）的同类镜像 Check 阶段是否也有此问题。
2. `shunit2` 在此 CI 环境中预期的安装路径是什么？`common_funs.sh:13` 是通过 `source` 还是通过绝对路径引用？
3. 该问题是否为 openEuler 24.03-LTS-SP4（该基础镜像版本较新）的 CI pipeline 首次运行暴露出的环境缺失？同仓库中其他已有 openEuler 24.03-LTS-SP4 镜像（如 `AI/oneapi-basekit`、`Others/activemq` 等）的 Check 阶段是否也因同样原因失败。

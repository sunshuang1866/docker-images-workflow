# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39 "CI工具依赖缺失" 同类，但缺失组件不同）
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段，位于 `common_funs.sh:13`
- 失败原因: CI runner 的 `eulerpublisher` 测试框架缺少 `shunit2` shell 单元测试库，导致容器构建后的验证测试（[Check] 阶段）无法执行而直接失败。Docker 镜像构建和推送（[Build] + [Push] 阶段）均已成功完成，无任何错误。

### 与 PR 变更的关联
**无关。** PR 新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Docker 镜像构建全过程（步骤 #1 ~ #11）全部成功完成，镜像已成功构建并推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败仅发生在 CI 后置检查阶段，原因是 CI runner 环境缺少 `shunit2`，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 包。`shunit2` 是 openEuler 仓库中的标准软件包，可通过 `dnf install shunit2 -y` 安装。此操作需由 CI 基础设施管理员在 runner 镜像或初始化脚本中完成，无需修改本仓库任何文件。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装但不在 `PATH` 中，可能需要在 `common_funs.sh` 中指定 `shunit2` 的绝对路径，或在 CI runner 的 `PATH` 环境变量中添加 `shunit2` 所在目录。

## 需要进一步确认的点
- 确认该 CI runner 的 OS 环境是否已安装 `shunit2`（执行 `rpm -qa | grep shunit2` 或 `which shunit2`）
- 确认 `eulerpublisher` 测试框架中对 `shunit2` 的依赖是否为新增，以及该测试框架的版本是否兼容当前 runner 环境
- 确认同一 CI 流水线中其他同架构镜像（如 24.03-lts-sp3 的 Go 镜像）的 [Check] 阶段是否也出现类似问题（以判断是 runner 级别还是镜像级问题）

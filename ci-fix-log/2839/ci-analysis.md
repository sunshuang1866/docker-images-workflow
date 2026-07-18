# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试编排工具 `eulerpublisher` 在 [Check] 阶段调用 `common_funs.sh` 脚本时，依赖的 `shunit2` shell 单元测试框架在 CI Runner 环境中未安装，导致测试框架初始化失败。Docker 镜像的构建（`#8 DONE 268.4s`）与推送（`[Push] finished`）均已成功完成，失败仅发生在后置检查阶段。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile 和 entrypoint.sh 完全正确——镜像构建和推送均顺利完成，PostgreSQL 17.6 从源码编译到 `make install` 全过程无错误。失败是因为 CI Runner 的测试环境缺少 `shunit2` 框架，属于 CI 基础设施问题。Check 结果表为空（无任何测试条目输出），进一步证明测试框架在初始化阶段即已崩溃，未进入实际测试。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 的测试镜像或预置环境中安装 `shunit2`。可通过如下途径之一：
- 在 Runner 置备脚本中添加 `dnf install -y shunit2` 或 `pip install shunit2`
- 确保 `eulerpublisher` 容器测试依赖中的 `shunit2` 二进制在 `PATH` 中可达
- 若 `shunit2` 应以本地脚本方式提供，在 `common_funs.sh` 所在目录部署 `shunit2` 脚本文件

## 需要进一步确认的点
- 确认 CI Runner（用于 24.03-lts-sp4 镜像检查的环境）中是否预装了 `shunit2`，以及 `common_funs.sh:13` 处引用 `shunit2` 的具体方式（`source`、`.`、还是直接命令调用）
- 确认同一 CI 流水线中其他 24.03-lts-sp4 镜像（非 postgres）的 Check 阶段是否存在相同的 `shunit2` 缺失问题，以判断是否为该 OS 版本 Runner 的全局缺陷

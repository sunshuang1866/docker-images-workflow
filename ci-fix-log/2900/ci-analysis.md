# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 的 `eulerpublisher` 测试框架在 [Check] 阶段尝试通过 `common_funs.sh` 脚本 source `shunit2` 测试库，但该库在 CI Runner 环境中不存在，导致容器镜像测试无法执行，检查表格为空，最终判定失败。

### 与 PR 变更的关联
**与 PR 变更无关**。Docker 镜像的构建（`#10 DONE 41.6s`）和推送（`#14 DONE 31.3s`）均已成功完成（日志中 `[Build] finished` / `[Push] finished`）。失败发生在 `eulerpublisher` 自身的测试框架初始化阶段——`shunit2` 是 CI Runner 环境需要预装的 shell 测试框架，非 Dockerfile 构建内容，也非本次 PR 新增文件。

## 修复方向

### 方向 1（置信度: 中）
在 CI Runner 节点上安装 `shunit2` 测试框架。`shunit2` 是一个标准的 shell 单元测试库，可通过系统包管理器安装（如 `yum install shunit2` 或 `apt install shunit2`），或手动下载放置在 `eulerpublisher` 测试框架预期的路径中。

### 方向 2（置信度: 低）
如果 CI Runner 环境中 `shunit2` 确实已安装但路径配置不正确，需检查 `common_funs.sh` 中引用 `shunit2` 的路径（如 `PATH` 环境变量或硬编码路径）是否与 Runner 实际安装位置一致。

## 需要进一步确认的点
1. 同一 CI 环境下其他镜像（如已有 httpd 2.4.66-oe2403sp2）的 [Check] 阶段是否同样因 `shunit2: file not found` 而失败，以此确认是全局 infra 问题还是仅本次构建 Runner 异常。
2. `shunit2` 在 CI Runner 上的预期安装路径，以及 `common_funs.sh` 第 13 行的具体 source 写法。
3. 该 `eulerpublisher` 版本的依赖清单中是否包含 `shunit2`，及其在 openEuler 仓库中的实际包名（可能为 `shunit2` 或 `shunit`）。

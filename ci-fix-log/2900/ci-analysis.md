# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: CI Runner 的 eulerpublisher 测试框架层
- 失败原因: CI 运行环境中缺少 `shunit2` shell 单元测试框架库，eulerpublisher 的 `[Check]` 阶段在 `common_funs.sh:13` 执行 `. shunit2` 时找不到该文件，导致测试框架无法初始化，所有测试项未能运行（Check 结果表为空）。镜像构建和推送阶段均已成功完成。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据，Docker 镜像构建（#9-#13 共 7 步全部 DONE）、导出和推送（#14 DONE）均成功完成。失败发生在 CI 测试框架 `eulerpublisher` 的 `[Check]` 阶段——该阶段尝试对已成功构建并推送的镜像运行容器测试，但因测试运行器本身缺少 `shunit2` 依赖而崩溃，无法执行任何测试。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 环境中安装 `shunit2` shell 单元测试框架。`shunit2` 通常可通过包管理器（如 `dnf install shunit2` 或 `apt install shunit2`）安装，或从 [GitHub](https://github.com/kward/shunit2) 手动部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 或框架预期的路径。此修复属于 CI 基础设施运维范畴，无需修改 PR 中的任何代码。

## 需要进一步确认的点
1. 确认 CI Runner 上 `shunit2` 的预期安装路径（如 `/usr/share/shunit2/shunit2` 或 `/usr/local/etc/eulerpublisher/tests/container/common/shunit2`），确保安装后路径与 `common_funs.sh` 中的 source 路径匹配。
2. 确认该失败是否为所有使用 openEuler 24.03-LTS-SP4 基镜像的新增 Dockerfile 的通用问题，或仅限特定 Runner 节点。
3. 镜像本身已成功构建并推送至 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`，如果容器测试环境短时间无法修复，可考虑手动拉取该镜像进行离线 smoke test 验证功能正确性。

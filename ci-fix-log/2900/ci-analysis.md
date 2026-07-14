# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 主机 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 基础设施的 `eulerpublisher` 测试框架在 [Check] 阶段尝试通过 `common_funs.sh` 脚本加载 `shunit2`（Shell 单元测试库），但该文件在 CI runner 主机上不存在，导致测试框架初始化失败，无法执行任何容器测试。

### 与 PR 变更的关联
**与 PR 无关。** PR #2900 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 下的 Dockerfile、启动脚本，以及相关文档和元数据条目。Docker 镜像的编译构建（`[Build]`）和推送（`[Push]`）均已成功完成，所有 Dockerfile 中的 RUN 步骤均执行完毕且无报错。失败发生在构建完成后 CI 的独立 [Check] 测试阶段，是 CI runner 环境缺少 `shunit2` 依赖导致的，与本次 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 主机上安装 `shunit2` Shell 测试框架。`shunit2` 通常可通过以下方式之一安装：
- 从 EPEL/openEuler 仓库安装：`dnf install shunit2`
- 或从源码部署到 CI runner 的预期路径下

该修复无需修改本次 PR 的任何文件，属于 CI 环境配置问题，应由 CI 基础设施维护者处理。

### 方向 2（置信度: 低）
如果 `shunit2` 此前在 CI runner 上可用、近期才丢失，可能存在 CI runner 镜像/环境退化（如最近一次 CI runner 更新移除了该包）。需排查 CI runner 的配置变更记录。

## 需要进一步确认的点
- `shunit2` 在 openEuler 24.03-LTS-SP4 的 yum/dnf 仓库中是否可用（包名可能是 `shunit2` 或 `shunit`）
- CI runner 主机上 `/usr/local/etc/eulerpublisher/tests/common/` 目录内容是否完整
- 其他使用同一 CI runner 的 PR 是否也同时出现此失败（可确认是否为 CI 环境全局退化）

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上 `shunit2`（Shell 单元测试框架）未安装或不在 `$PATH` 中，导致 `eulerpublisher` 的 [Check] 阶段无法启动任何容器功能验证测试。Docker 镜像构建和推送（[Build] + [Push]）均已成功完成，失败仅发生在后置测试阶段。

### 与 PR 变更的关联
**无关联**。PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及辅助文件（httpd-foreground、meta.yml、README.md、image-info.yml）。Docker 构建全部 7 个步骤均成功完成（#9 DONE ~77s, #10 DONE 41.6s, #11 DONE 0.1s, #12 DONE 0.0s, #13 DONE 0.1s），镜像已成功推送到 registry（#14 DONE 31.3s）。`shunit2: file not found` 是 CI runner 环境层面的基础设施缺失，与本次 PR 的代码改动无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 框架。`shunit2` 是 `eulerpublisher` 容器测试套件的核心依赖（`common_funs.sh` 第 13 行通过 `.` 命令 source 它）。安装方式通常为：
- 从 EPEL/openEuler 仓库安装：`dnf install shunit2`
- 或手动下载 shunit2 脚本文件到系统路径（如 `/usr/share/shunit2/shunit2`）并确保 CI runner 环境变量或软链使其可被 source 找到

### 方向 2（置信度: 低）
如果 CI runner 环境无法安装 shunit2，`eulerpublisher` 测试套件可改为将 shunit2 作为自身依赖打包/携带，使其不依赖宿主系统预装。

## 需要进一步确认的点
- 确认 CI runner 节点上是否已安装 `shunit2` 包，以及其安装路径是否在 `common_funs.sh` 预期的搜索路径中
- 确认该 CI runner 是否为 x86_64 架构专属节点（日志显示镜像是 `httpd:2.4.66-oe2403sp4-x86_64`），以及 aarch64 节点是否存在同样问题
- 确认同一 CI runner 上其他 PR 的 [Check] 阶段是否也失败（判断是此次新增 SP4 触发还是已有系统性问题）

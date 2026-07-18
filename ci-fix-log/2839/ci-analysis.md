# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13（CI Runner 宿主环境）
- 失败原因: CI Runner 的 `eulerpublisher` 测试框架在 [Check] 阶段执行 `common_funs.sh` 时尝试加载 `shunit2`（Shell 单元测试框架），但该工具未安装在该 CI 节点上，导致 Check 阶段初始化即失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 和 entrypoint.sh 本身没有问题：

- Docker 构建阶段（[Build]）完全成功：PostgreSQL 17.6 源码在 openEuler 24.03-LTS-SP4 基础镜像上完成 `./configure → make → make install` 全流程编译，所有 bin 工具安装到位，镜像构建并导出成功（`#8 DONE 268.4s`, `#11 DONE 58.0s`）。
- 镜像推送阶段（[Push]）完全成功：镜像 `17.6-oe2403sp4-x86_64` 已推送到 registry。
- 失败发生在独立的 [Check] 阶段，该阶段由 `eulerpublisher` 工具的测试框架执行，因 CI 节点缺少 `shunit2` 包而无法启动，**从未实际运行任何容器功能测试**。

## 修复方向

### 方向 1（置信度: 高）
在 CI 执行 [Check] 阶段的 runner 节点上安装 `shunit2` 包。具体操作：在 `eulerpublisher` 部署脚本或 CI runner 初始化脚本中补充 `dnf install -y shunit2`（或等效命令），并确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能正确引用到已安装的 `shunit2` 库文件（通常为 `/usr/share/shunit2/shunit2` 或类似路径）。

### 方向 2（置信度: 低）
如果 `shunit2` 确实已安装但路径不对，检查 `common_funs.sh` 中 `shunit2` 的 source 路径是否与实际安装路径一致（注意不同 openEuler 版本间 shunit2 安装路径可能变化），必要时调整脚本中的 source 路径。

## 需要进一步确认的点
1. 该 CI 节点的 openEuler 版本是否与 24.03-LTS-SP4 镜像的测试环境匹配。`shunit2` 在 openEuler 24.03 系列中的 RPM 包名和安装路径是否与测试脚本硬编码的路径一致。
2. 如果是新 OS 版本的 CI runner 节点首次执行 Check，是否需要将该 runner 节点加入 `eulerpublisher` 依赖安装的初始化流程中。
3. 排除容器本身的启动/运行问题——由于 Check 阶段在加载测试框架时就失败了，无法判断容器是否能正常启动。待 `shunit2` 修复后，需重新触发 CI 验证容器功能是否正常。

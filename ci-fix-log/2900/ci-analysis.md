# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed, eulerpublisher

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境中的测试框架脚本 `common_funs.sh` 尝试通过 `.` 命令 source 加载 `shunit2`，但 `shunit2` 未安装在 CI runner 上，导致 Check 阶段立即失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（httpd-foreground、README.md、image-info.yml、meta.yml），所有 Docker 构建步骤（#9 source 解压、#10 configure/make/make install、#11 groupadd/useradd 配置 sed、#12 COPY httpd-foreground、#13 chmod）均**成功完成**，镜像已成功构建并推送（`[Build] finished`、`[Push] finished`）。失败仅发生在 CI 编排工具的后置 Check 验证阶段，该阶段的 `shunit2` 依赖缺失属于 CI 基础设施问题，与 PR 代码改动无因果关联。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员需在运行 openEuler 24.03-LTS-SP4 相关镜像构建的 runner 节点上安装 `shunit2` 测试框架包（可通过 `dnf install shunit2` 或手动部署到 `common_funs.sh` 可 source 到的路径），消除 Check 阶段的依赖缺失错误。该修复在 CI 基础设施侧完成，无需修改任何仓库文件。

## 需要进一步确认的点
- 确认 `shunit2` 在本次使用的 CI runner（构建 openEuler 24.03-LTS-SP4 镜像的节点）上是否确实未安装，以及是否存在针对 SP4 架构 runner 的独立测试环境初始化流程。
- 确认同类 httpd 的其他版本（如 SP2）在 Check 阶段是否也会执行 `shunit2` 测试，如果是且均通过，则此次 SP4 失败可能是因 runner 环境未完成测试框架部署。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, [Check] test failed

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段中 `eulerpublisher` 测试框架的 `common_funs.sh` 脚本在第 13 行尝试 `source shunit2`，但 `shunit2`（shell 单元测试框架）在 CI runner 的环境中不可用，导致 Check 阶段异常退出。Docker 镜像构建和推送本身均已成功完成（#10 DONE 41.6s，#11~#13 DONE，exporting/pushing 完成，`[Build] finished`，`[Push] finished`）。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-lts-sp4 上的 Dockerfile、httpd-foreground 启动脚本，并更新了 meta.yml、image-info.yml、README.md。所有 Docker 构建步骤（#1~#13）全部成功，镜像已成功构建并推送。失败发生在 eulerpublisher 工具的后处理/验证（[Check]）阶段，原因是 CI runner 上缺少 `shunit2` 测试库。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 `shunit2` 包。在 openEuler 系统上可通过 `dnf install shunit2` 或 `yum install shunit2` 安装，或将其加入 CI 镜像的预装依赖列表。`shunit2` 的 `source` 路径在 `common_funs.sh` 中使用的是无路径前缀的简写形式（`. shunit2`），依赖于 `PATH` 环境变量或 `shunit2` 已被安装到系统标准 Shell 库路径。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装但不在 `common_funs.sh` 期望的路径中，可能是 `common_funs.sh` 第 13 行的 source 路径不正确，需要调整为 `shunit2` 的实际安装路径（如 `/usr/share/shunit2/shunit2`）。

## 需要进一步确认的点
1. CI runner 环境中是否已安装 `shunit2` 包？若已安装，确认其安装路径与 `common_funs.sh` 中预期的路径一致。
2. 该 Check 步骤在其他同类 PR（例如同仓库中其他 24.03-lts-sp4 的 Dockerfile）上是否也失败了？如果其他 PR 的 Check 正常，则可能是本次特定 runner 节点的环境问题。
3. `common_funs.sh` 中的 `shunit2` source 语句是否依赖于从被测试镜像的目录结构中查找 `shunit2` 的文件（而非系统库）？如果是，PR 新增目录下缺少本地 `shunit2` 副本也可能是原因。

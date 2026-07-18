# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, Check test failed, eulerpublisher

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner Check 阶段（`eulerpublisher` 容器测试，`common_funs.sh:13`）
- 失败原因: CI runner 节点上缺少 `shunit2`（shell 单元测试框架），`common_funs.sh` 第 13 行 `source shunit2` 时找不到该文件，导致容器 Check 测试流程无法启动。Docker 镜像构建和推送阶段均已成功完成（`[Build] finished`、`[Push] finished`），与 PR 代码变更无关。

### 与 PR 变更的关联
**无关。** Docker 镜像构建全流程（源码下载、编译、安装、配置、导出、推送）全部成功：

- `#10 DONE 41.6s` — httpd 2.4.66 编译及 `make install` 成功
- `#11 DONE 0.1s` — `groupadd`/`useradd`/`sed` 配置成功
- `#12 DONE 0.0s` — `COPY httpd-foreground` 成功
- `#13 DONE 0.1s` — `chmod` 成功
- `#14 DONE 31.3s` — 镜像导出和推送成功

失败唯一发生在 CI 流水线末尾的 `[Check]` 阶段（容器启动测试），根因为 CI runner 环境缺少 `shunit2`，与 PR 新增的 Dockerfile、httpd-foreground 脚本、meta.yml 等文件均无直接关联。

## 修复方向

### 方向 1（置信度: 高）
**无需任何代码修改。** 此失败为 CI 基础设施问题。需运维人员在执行容器检测的 CI runner 节点上安装 `shunit2` 包（如 `dnf install shunit2`），然后重新触发构建。

### 方向 2（置信度: 低）
若 `shunit2` 已安装但仍报 `file not found`，需排查 `eulerpublisher` 测试脚本中 `shunit2` 的 source 路径配置——`common_funs.sh:13` 是否为相对路径引用，存在路径查找失败的场景。

## 需要进一步确认的点
1. CI runner 节点上 `shunit2` 是否已安装（运行 `which shunit2` 或 `rpm -qa | grep shunit2` 确认）
2. 该 runner 上同一时段其他 PR 的 Check 阶段是否也出现相同错误（判断是单节点问题还是全局配置变更）
3. `eulerpublisher` 测试框架中 `shunit2` 的预期安装路径与 `common_funs.sh` 中 source 路径是否一致

## 修复验证要求
不适用。此失败为 infra-error，无需修改 PR 代码，无需验证正则在目标文件中的匹配。

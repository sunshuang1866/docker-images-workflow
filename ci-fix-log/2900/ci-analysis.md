# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试阶段（`[Check]`）中，测试框架 `eulerpublisher` 在运行容器检查脚本时尝试 `source shunit2`，但 CI Runner 上未安装或未正确配置 `shunit2` shell 测试框架，导致测试套件无法加载，`[Check]` 直接失败。

### 与 PR 变更的关联
**PR 变更与此次失败无关**。该 PR 仅做了以下新增操作：
- 新增 Dockerfile（`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`）——从源码编译 httpd 2.4.66
- 新增 `httpd-foreground` 启动脚本
- 更新 README.md、`doc/image-info.yml`、`meta.yml` 的条目

Docker 镜像构建阶段（所有 7 个 RUN 步骤）和推送阶段均**成功完成**（日志中 `#13 DONE 0.1s`、`[Build] finished`、`[Push] finished`、`#14 exporting manifest list ... done`）。失败仅发生在 CI 流水线后续的 `[Check]` 测试阶段，且错误为 CI Runner 基础设施缺失 `shunit2`，与 Dockerfile 内容、构建参数、源码均无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 节点上安装 `shunit2` 包。对于 openEuler 环境，可通过 `yum install -y shunit2` 或 `yum install -y shunit` 安装。若包名不同，需在 CI Runner 上确认正确的包名后安装。

### 方向 2（置信度: 中）
若 `shunit2` 已安装但路径不匹配，检查 CI Runner 上 `common_funs.sh` 第 13 行的 `source` 路径是否正确，并与实际安装路径对齐。

## 需要进一步确认的点
- CI Runner 节点上 `shunit2` 是否已安装（`rpm -qa | grep shunit`）
- 若已安装，其实际安装路径（`find / -name "shunit2" 2>/dev/null`）与 `common_funs.sh` 中 source 的路径是否一致
- 同一 CI Runner 上其他同类 httpd 镜像（如 `2.4.66-oe2403sp2`）的 `[Check]` 阶段是否同样因 shunit2 缺失而失败——如果是，说明是 Runner 环境整体问题，非本 PR 独有

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: CI 环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（eulerpublisher 测试框架通用函数脚本）
- 失败原因: CI 测试阶段（`[Check]`）尝试运行镜像验证测试时，`common_funs.sh` 第 13 行尝试 `. source shunit2` 加载 shunit2 测试框架库，但该文件在 CI runner 上不存在，导致测试脚本无法执行，`eulerpublisher` 报告 `[Check] test failed`

### 与 PR 变更的关联
**与 PR 变更无关。** 该失败发生在 CI 基础设施层面：

1. Docker 镜像构建（步骤 #1–#7）全部成功完成 — 源码下载、configure、make、make install、配置文件修改均无错误
2. 镜像推送到 registry 成功（`[Push] finished`）
3. 失败仅发生在构建完成后的 `[Check]` 测试阶段，原因是 CI runner 上缺少 `shunit2` shell 测试框架包，导致镜像验证脚本无法启动

PR 仅新增了 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`、`httpd-foreground` 脚本以及相关元数据文件（README.md、image-info.yml、meta.yml），这些变更不涉及 CI 测试框架配置，也不可能导致 `shunit2` 缺失。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2`（shUnit2 shell 单元测试框架）包，或确认为 eulerpublisher 测试运行环境补齐该依赖。这不是代码层面的修复，而是 CI 基础设施运维操作。

### 方向 2（置信度: 低）
不排除该 CI runner 节点存在环境残缺的个别情况，可尝试重新触发 CI 运行，确认是否为偶发性基础设施故障。

## 需要进一步确认的点
- 同一时期其他 PR 的 CI `[Check]` 阶段是否也因 `shunit2: file not found` 失败？如果其他 PR 检查正常通过，则可能是特定 runner 节点或该 PR 触发的特定 runner 实例存在问题
- `shunit2` 在此 CI 环境中应为预装依赖还是由 eulerpublisher 自行管理？需确认该缺失是近期环境变更引入还是长期存在

# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（参考模式39：CI工具依赖缺失）
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, check failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

随后 [Check] 测试结果表完全为空（无任何 Check Items 被加载），进一步证实测试框架因 `shunit2` 缺失未能初始化：
```
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI [Check] 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上的测试基础设施缺少 `shunit2` shell 测试框架，`common_funs.sh` 第13行尝试加载 `shunit2` 时失败，导致整个 [Check] 阶段无法执行。

### 与 PR 变更的关联
PR 变更与 CI 失败**无关**。证据如下：
- Docker 镜像构建完全成功（`#8 DONE 268.4s`，PostgreSQL 17.6 编译安装无误）
- Docker 镜像推送完全成功（`#11 DONE 58.0s`，manifest 已推送至 registry）
- eulerpublisher 工具日志明确显示 `[Build] finished` 和 `[Push] finished`
- 失败仅发生在 [Check] 阶段，且错误为 `shunit2: No such file or directory`——这是 CI 测试框架自身的依赖缺失，与 Dockerfile、entrypoint.sh、README.md、meta.yml 中新增的任何内容无关

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施团队需在构建 runner 上安装 `shunit2` 测试框架。可选方式：
- 在 openEuler 24.03-LTS-SP4 基础环境中通过包管理器安装（如 `dnf install shunit2`）
- 或将 shunit2 脚本部署到 `common_funs.sh` 能找到的预期路径
- 若该 runner 为临时构建环境，需在 provision 脚本中添加 shunit2 的安装步骤

此问题非 PR 代码变更所致，无需修改 Dockerfile、entrypoint.sh、README.md 或 meta.yml。

## 需要进一步确认的点
1. 该 CI runner 上是否安装了 `shunit2`，若已安装，确认安装路径是否与 `common_funs.sh:13` 中 `source`/`.` 引用的路径一致
2. 该问题是否仅影响本次构建的特定 runner，还是所有 openEuler 容器镜像 CI runner 的共性问题（可通过查看同批次其他镜像的构建日志交叉验证）
3. `common_funs.sh` 第13行的具体内容是什么（`source shunit2` 还是 `. /path/to/shunit2`），以确定正确的修复方式

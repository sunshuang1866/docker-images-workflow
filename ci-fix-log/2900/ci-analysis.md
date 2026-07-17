# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed, eulerpublisher

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架公共脚本）
- 失败原因: CI runner 上缺少 `shunit2` 单元测试框架库文件。在 [Build] 和 [Push] 阶段均已成功后，[Check] 阶段的测试脚本 `common_funs.sh` 第 13 行尝试 `source shunit2`，但该文件在 CI runner 的文件系统中不存在，导致整个 [Check] 阶段崩溃（Check Items 表格为空，无任何测试用例执行）。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（`#14 DONE 31.3s`）和推送（`[Push] finished`）均已完成，httpd 2.4.66 镜像在 openEuler 24.03-LTS-SP4 上从源码编译到 `make install` 全部成功。失败发生在 CI 基础设施侧——`eulerpublisher` 工具的 [Check] 阶段因测试框架依赖缺失而崩溃，与 PR 新增的 Dockerfile、httpd-foreground 脚本、meta.yml 等文件无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` 测试框架包（例如 `dnf install shunit2` 或从 GitHub 克隆 `kward/shunit2` 到 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 路径下），确保 CI [Check] 阶段可以正常加载测试框架并执行容器功能验证。

## 需要进一步确认的点
1. 确认 CI runner 镜像中 `shunit2` 的预期安装路径与 `common_funs.sh` 第 13 行 source 的目标路径是否一致。
2. 确认是否仅有 24.03-LTS-SP4 对应的 runner 缺少该依赖，还是全局 CI runner 均受影响。
3. 若该 CI runner 是临时创建的环境，可能需要将 `shunit2` 加入 CI 环境的初始化脚本或 Dockerfile 中。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——此为 CI 基础设施依赖缺失，无需修改 PR 代码。

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 测试框架 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试运行环境中缺少 `shunit2`（Shell 单元测试框架），导致测试脚本无法初始化，所有 Check 项目返回空表，最终 CI 判定 `[Check] test failed`

### 与 PR 变更的关联
与 PR 代码变更**无关**。证据如下：
1. Docker 镜像构建（`./configure && make && make install`）和推送均完全成功（`#14 DONE 31.3s`，`[Build] finished`，`[Push] finished`）
2. 日志中唯一的 Docker 级告警 `LegacyKeyValueFormat`（第 5 行 `ENV key value` 格式）仅为 lint 级 warning，不影响构建结果
3. 失败发生在 `[Check]` 阶段——CI 编排工具 `eulerpublisher` 在构建完成后启动容器检验脚本时，因测试框架 `shunit2` 未安装在 CI runner 上，导致检验脚本初始化失败
4. PR 仅新增 Dockerfile、httpd-foreground 脚本及元数据文件（meta.yml、README.md、image-info.yml），不涉及 CI 基础设施配置

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境或测试容器镜像中安装 `shunit2`（Shell 单元测试框架）。这是 CI 基础设施层面的问题，**Code Fixer 无需处理**，应由 CI 运维团队确保测试运行环境具备 `shunit2` 依赖。

## 需要进一步确认的点
- 确认 `shunit2` 在其他同仓库镜像的 CI Check 阶段是否也存在缺失但被静默跳过的情况
- 确认 CI runner 镜像模板中是否遗漏了 `shunit2` 的安装步骤，还是本次使用的 runner 实例异常
- 若确认 `shunit2` 是本次 openEuler 24.03-LTS-SP4 基镜像的 CI runner 特有问题（而 22.03/24.03-SP2/SP3 等正常），则需联系 CI 运维为 SP4 runner 补充 shunit2 依赖

# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shutil2: file not found`, `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`, `line 13: .:`

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shutil2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 上 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI 测试框架脚本，非 PR 代码）
- 失败原因: CI 的 `[Check]` 阶段执行容器测试脚本时，`common_funs.sh` 第 13 行尝试 `. source` 加载 `shunit2`（日志中显示为 `shutil2`，疑为终端输出混淆或别名），该文件在 CI runner 环境中不存在，导致测试框架初始化失败，所有 check items 为空（测试未实际运行）

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 新增的 httpd Dockerfile 构建和推送均成功完成（日志中 `#10 DONE 41.6s`、`#14 pushing manifest ... done`、`[Build] finished`、`[Push] finished`），Docker 镜像 `****test/httpd:2.4.66-oe2403sp4-x86_64` 已成功构建并推送至 registry。失败发生在 `[Check]` 阶段，是 CI runner 缺少 `shunit2`（shell 单元测试库）导致的 CI 基础设施问题，与 PR 的 Dockerfile、meta.yml、README.md 等变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 节点上安装 `shunit2` 包（openEuler 上可通过 `yum install shunit2` 或 `dnf install shunit2` 安装），确保 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下存在 `shunit2` 文件或系统 PATH 中可找到该命令。若日志中的 `shutil2` 是脚本中的真实文件名（而非 `shunit2` 的终端输出混淆），则需确认该文件在 CI 环境中的部署方式。

### 方向 2（置信度: 低）
若 `shunit2` 已正确安装但仍报错，可能是 `common_funs.sh` 中的 source 路径相对于测试工作目录不正确，需检查 CI 测试的启动脚本是否正确设置了 `PATH` 环境变量或工作目录。

## 需要进一步确认的点
1. CI runner 上 `shunit2` 包是否已安装（`which shunit2` 或 `rpm -qa | grep shunit2`）
2. `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下是否存在 `shunit2`（或 `shutil2`）文件
3. 同类其他 openEuler 24.03-LTS-SP4 镜像（如 SP2、SP3）的 CI check 阶段是否也报同样错误（可交叉验证是否为该 runner 节点的普遍问题）
4. 日志中的 `shutil2` 是否为终端输出渲染问题（如 `shunit2` 因字体/编码被错误显示），建议查看 CI raw log 确认真实文件名

## 修复验证要求
不适用——本失败为 CI 基础设施问题（infra-error），Code Fixer 无需处理 PR 代码，需由 CI 运维团队检查 runner 环境。

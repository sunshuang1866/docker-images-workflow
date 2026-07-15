# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `/bin/sh^M`, bad interpreter, CRLF, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段，测试脚本 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`
- 失败原因: eulerpublisher CI 工具链中的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，`\r\n`），导致 shebang 行被解析为 `#!/bin/sh\r`，系统将 `\r`（显示为 `^M`）识别为解释器路径的一部分，找不到有效的解释器而报 "bad interpreter" 错误。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的代码变更（新增 Dockerfile、更新 README.md、image-info.yml、meta.yml）均为正确的镜像元数据和构建逻辑。日志显示 Docker 镜像构建和推送均已成功完成：
```
2026-07-10 11:58:05,860 - INFO - [Build] finished
2026-07-10 11:58:05,860 - INFO - [Push] finished
```
失败仅发生在 eulerpublisher 的 Check 阶段，根因是 CI 基础设施中测试脚本的换行符问题，不是 PR 代码变更引起。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施（eulerpublisher 仓库）中的 `tests/container/app/bwa_test.sh` 测试脚本被写入了 CRLF 换行符。需要对该文件执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换换行符为 LF，然后重新部署 eulerpublisher 包。

### 方向 2（置信度: 低）
如果 `bwa_test.sh` 脚本尚不存在于 eulerpublisher 仓库中（即需为 bwa 镜像的 Check 阶段新增），则可能在上传/签出过程中引入了错误的换行符。需确认脚本来源并修正换行符。

## 需要进一步确认的点
- 确认 eulerpublisher 仓库中 `tests/container/app/bwa_test.sh` 脚本的实际换行符状态（CRLF 还是 LF）
- 确认该脚本是已存在脚本的换行符问题还是本次新上传脚本的问题
- 确认 CI runner 上 eulerpublisher 包的安装/更新方式（git clone 还是 pip install），以确定如何修复脚本并使其生效

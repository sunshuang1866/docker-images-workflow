# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: `bad interpreter`, `^M`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
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
- 失败位置: `/etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 框架 `eulerpublisher` 的内置测试脚本，非 PR 文件）
- 失败原因: `bwa_test.sh` 文件首行 shebang `#!/bin/sh` 末尾带有 Windows 风格的换行符 `\r`（`^M`），导致系统查找名为 `/bin/sh\r` 的解释器，该解释器不存在，执行失败。

### 与 PR 变更的关联
**与 PR 无关**。该 PR 仅新增 Dockerfile 和更新元数据文件（README.md、image-info.yml、meta.yml），所有变更均为纯文本/配置，不涉及任何测试脚本。Docker 镜像的构建和推送均已成功（日志中 `#7 DONE 199.0s`，`[Build] finished`，`[Push] finished`）。失败发生在 CI 框架 `eulerpublisher` 的 [Check] 阶段，其内置测试脚本 `bwa_test.sh` 自身存在 CRLF 行尾问题，属于 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护者需要修复 `eulerpublisher` 包中的 `bwa_test.sh` 文件，将其从 CRLF 换行符转换为 LF。执行 `dos2unix` 或等效操作重新打包/更新 `eulerpublisher` 包，或使用 `sed -i 's/\r$//' bwa_test.sh` 清除回车符。该修复与 PR 代码无关，PR 的 Dockerfile 无需任何修改。

## 需要进一步确认的点
1. `eulerpublisher` 包的打包/构建流程中是否存在跨平台问题（如在 Windows 上生成 `.sh` 测试脚本后打包），导致 CRLF 行尾混入 Linux 包。
2. 其他应用镜像（非 bwa 镜像）的 Check 阶段是否也受同类问题影响但尚未暴露。
3. 该 `bwa_test.sh` 是 eulerpublisher 包中已存在的老版本脚本，还是本次 CI 运行时动态生成的，若是后者需排查生成逻辑。

# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试脚本 CRLF 换行符
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh, CRLF

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher 包内的 CI 测试脚本）
- 失败原因: CI 编排工具 `eulerpublisher` 包中自带的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF）。脚本 shebang 行 `#!/bin/sh` 末尾携带了不可见的回车符 `\r`（^M），导致内核将解释器路径解析为 `/bin/sh\r`（含回车符），该路径不存在，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile 和更新了三个元数据文件（README.md、image-info.yml、meta.yml），均不涉及 `bwa_test.sh` 脚本。Docker 镜像的构建和推送阶段均成功完成（日志中可见 `#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`），失败发生在 CI 的后处理 [Check] 阶段，由 eulerpublisher 包内置的测试脚本自身换行符格式错误导致。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需修改 PR 代码。需要 CI 管理员修复 eulerpublisher 包中的 `bwa_test.sh` 文件，将其换行符从 CRLF（Windows）转换为 LF（Unix）。可以在 CI runner 上执行 `dos2unix` 或 `sed -i 's/\r$//'` 命令处理该文件，或从源头确保 eulerpublisher 包发布时包含 Unix 换行符的脚本文件。

## 需要进一步确认的点
1. 确认 eulerpublisher 包中 `bwa_test.sh` 是否为新近引入的脚本，或者是否该脚本在最近的包更新中意外被转为 CRLF 格式。
2. 确认同批次的其他镜像 PR（非 bwa）是否也因同一脚本问题在 [Check] 阶段失败——如果是，则进一步印证为基础设施问题。
3. `CMD ["bwa"]` 会导致容器启动后 bwa 立即打印帮助并退出（非持久化进程），即使测试脚本修复后，[Check] 测试也可能因容器提前退出而失败。建议在 test 脚本修复后观察一轮 CI 结果来排除此隐患。

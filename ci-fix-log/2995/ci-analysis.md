# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行符
- 新模式症状关键词: bad interpreter, No such file or directory, ^M, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher` CI 工具的 [Check] 阶段，执行测试脚本 `bwa_test.sh` 时
- 失败原因: `eulerpublisher` 包中安装的测试脚本 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 包含 Windows 风格的 CRLF 换行符（`\r\n`）。shebang 行 `#!/bin/sh` 被 Linux 内核解析为 `#!/bin/sh\r`，内核尝试查找名为 `/bin/sh\r` 的解释器失败，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建和推送阶段均完全成功（`[Build] finished`、`[Push] finished`）。失败发生在 CI 后置 [Check] 阶段，由 `eulerpublisher` 包内携带的测试脚本格式问题触发，属于 CI 基础设施问题。PR 作者未修改且无法控制该测试脚本。

## 修复方向

### 方向 1（置信度: 高）
`eulerpublisher` 包维护者需要将 `tests/container/app/bwa_test.sh` 转换为 Unix 换行符（LF），可使用 `dos2unix` 或 `sed -i 's/\r$//'` 处理该文件后重新打包发布。此问题不在本仓库范围内，CI 流水线维护方需修复 `eulerpublisher` 包。

### 方向 2（置信度: 中）
如果 `bwa_test.sh` 不存在于 `eulerpublisher` 包中，而是由 CI 框架动态创建/拷贝生成，则需检查 CI 脚本中的文件生成逻辑是否存在引入 CRLF 的问题（如 Git 的 `core.autocrlf` 设置导致 checkout 时自动转换换行符）。

## 需要进一步确认的点
1. `bwa_test.sh` 文件来源：该文件是由 `eulerpublisher` pip 包安装的，还是由 CI 流水线克隆的 `eulerpublisher` Git 仓库中携带的？
2. 该文件是否仅对 bwa 镜像有此问题（其他镜像的 `*_test.sh` 是否正常），以判断是单个文件格式异常还是整个包都存在 CRLF 问题。
3. CI 构建节点的 Git 配置中 `core.autocrlf` 是否被设置为 `true`，导致 clone 时自动将 LF 转为 CRLF。

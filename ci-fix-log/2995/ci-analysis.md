# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF编码
- 新模式症状关键词: bad interpreter, ^M, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 基础设施安装的测试脚本，非 PR 变更文件）
- 失败原因: CI 工具链 `eulerpublisher` 中安装的 bwa 测试脚本 `bwa_test.sh` 带有 Windows 换行符（CRLF, `\r\n`），导致 shebang 行被解析为 `/bin/sh\r`，操作系统找不到该解释器，报 "bad interpreter: No such file or directory"。

### 与 PR 变更的关联
**与本次 PR 代码变更无关。** 理由如下：

1. Docker 镜像构建完全成功：日志显示 `#7 DONE 199.0s`，make 编译 bwa 0.7.18 顺利通过，构建产物已推送到 Docker registry（`[Build] finished`、`[Push] finished`）。
2. 失败发生在 CI 后置检查阶段（`[Check]` 步骤），该阶段调用的是 CI 工具链 `eulerpublisher` 预装目录下的测试脚本 `bwa_test.sh`，该脚本不在本 PR 变更范围内，也不由 PR 生成或控制。
3. PR 仅新增/修改了 `HPC/bwa/` 下的 Dockerfile、README.md、image-info.yml、meta.yml 四个文件，均不涉及测试脚本或行尾编码。

## 修复方向

### 方向 1（置信度: 高）
**修复对象不在本仓库，而在 CI 基础设施侧。** 需要 CI 运维人员检查 `eulerpublisher` Python 包中打包的 `bwa_test.sh` 文件，将其行尾从 CRLF 转换为 LF（Unix 格式）。典型修复命令：

```bash
sed -i 's/\r$//' /usr/etc/eulerpublisher/tests/container/app/bwa_test.sh
```

或在 `eulerpublisher` 包源码中确保测试脚本以 Unix 行尾保存后重新打包/部署。

## 需要进一步确认的点
1. 确认 `bwa_test.sh` 的 CRLF 是 `eulerpublisher` 包打包时的源码问题，还是 CI 节点部署时的拷贝/检出不慎导致的。
2. 检查同一 `eulerpublisher` 安装路径下其他 `*_test.sh` 文件是否也存在同样的 CRLF 问题，如有应一并修复。
3. 确认该 CI 节点在其他 bwa 相关 PR（如已有的 22.03-lts-sp3）构建中是否也曾因同一 `bwa_test.sh` 失败，或本 PR 是否首次触发该测试脚本。

## 修复验证要求
本失败为 infra-error，修复不涉及 PR 代码变更。若 CI 运维修复了 `bwa_test.sh` 的行尾编码后，建议对本 PR 重新触发 CI 构建以验证通过。

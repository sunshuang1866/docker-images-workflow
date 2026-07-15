# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符异常
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段，测试脚本 `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（实际路径 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`）
- 失败原因: 测试脚本 `bwa_test.sh` 的 shebang 行使用了 Windows 风格换行符（CRLF，即 `\r\n`），导致内核将解释器路径解析为 `/bin/sh\r`（末尾含回车符），该路径不存在，触发 `bad interpreter: No such file or directory` 错误

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、README 更新、image-info.yml 和 meta.yml。日志中 Docker 镜像构建（`#7 DONE 199.0s`）和推送（`[Push] finished`）均已成功完成。失败发生在 CI 基础设施 `eulerpublisher` 包的 Check 阶段，因为 `bwa_test.sh` 测试脚本本身存在 CRLF 换行符问题，与本次 PR 的代码改动无关。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施维护方需要将 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本的换行符从 CRLF 转换为 LF（在 Linux CI runner 上执行 `dos2unix` 或 `sed -i 's/\r$//'` 对该文件进行处理，或修复上游 eulerpublisher 仓库中该文件的提交，确保以 LF 换行符存储）。

### 方向 2（置信度: 低）
若 bwa_test.sh 是从 eulerpublisher Git 仓库 `git clone` 得到的新增文件（非系统预装包），则可能是 Git 客户端配置了 `core.autocrlf=true` 导致自动转换，需检查 CI runner 的 Git 配置并将 `bwa_test.sh` 加入 `.gitattributes` 显式声明为 LF 格式。

## 需要进一步确认的点
- 确认 `bwa_test.sh` 文件是来自系统安装的 `eulerpublisher` RPM 包，还是来自 CI 流程中 `git clone` 的 eulerpublisher 源码仓库
- 确认是否只有 `bwa_test.sh` 受 CRLF 影响，还是 eulerpublisher 测试套件中其他测试脚本也有同类问题
- 如果问题出在上游 eulerpublisher 仓库，需确认该文件是否是最近才新增的（如果 bwa 在 24.03-LTS-SP4 之前没有对应的测试脚本，则该脚本可能为新近添加且提交时带入了 CRLF）

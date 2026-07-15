# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF行尾
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
#7 DONE 199.0s
#8 exporting to image ... done
#8 pushing manifest ... done
[Build] finished
[Push] finished
[Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 工具 `eulerpublisher` 包内的测试脚本）
- 失败原因: `eulerpublisher` 包中自带的 `bwa_test.sh` 测试脚本使用 Windows 风格 CRLF（`\r\n`）换行符，导致 shebang `#!/bin/sh` 被 Linux 内核解析为 `#!/bin/sh\r`，`/bin/sh\r` 不是有效解释器，无法执行该脚本。Docker 镜像的构建和推送阶段均已完成并成功，失败仅发生在 CI 的 `[Check]` 后置测试阶段。

### 与 PR 变更的关联
**此失败与 PR 代码变更无关。** Docker 镜像构建全流程（yum 安装依赖 → 下载 bwa 源码 → 编译 → 安装二进制 → 清理构建依赖 → 推送镜像）在日志中全部成功完成（`#7 DONE 199.0s`、`[Build] finished`、`[Push] finished`）。`bwa_test.sh` 脚本位于 eulerpublisher 的 pip 安装路径下，是 CI 工具链的组件，不在 PR 仓库中，也不由 PR 的 diff 引入。

## 修复方向

### 方向 1（置信度: 中）
这是 CI 基础设施问题。`eulerpublisher` 包的 `bwa_test.sh` 文件在打包或安装到 CI runner 时带了 CRLF 行尾。需联系 CI 平台的维护者/打包者，确认 eulerpublisher 的 `tests/container/app/bwa_test.sh` 源文件是否以 CRLF 存储，若是则转换为 LF 后重新发布该包。

### 方向 2（置信度: 低）
若 `bwa_test.sh` 脚本是在 CI 运行期间从 Git 仓库检出（而非从 pip 包释放），可能是 Git 在 checkout 时的 `core.autocrlf` 设置不当导致换行符被转换为 CRLF。需检查 CI runner 上 eulerpublisher 仓库 clone 时的 Git 配置。

## 需要进一步确认的点
- `bwa_test.sh` 的来源：确认该脚本是从 pip 安装的 `eulerpublisher` wheel/sdist 中释放出来的，还是在 CI 流程运行时从某个 Git 仓库动态检出并复制到该路径的。
- 该问题是否影响其他镜像的 CI 检查：如果 eulerpublisher 包中多个测试脚本均有 CRLF 问题，则这是一个系统性 pip 打包缺陷；若仅 `bwa_test.sh` 受影响，需追溯该文件的上游变更记录。
- 建议获取 eulerpublisher 包的源码仓库，检查 `tests/container/app/bwa_test.sh` 文件的原始行尾格式（是否为 CRLF），以确定根因是在源码侧还是 CI 环境侧。

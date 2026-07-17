# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Check阶段缺少shunit2
- 新模式症状关键词: shunit2: No such file or directory, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 编排工具 `eulerpublisher` 在执行 `[Check]` 阶段时，`common_funs.sh` 尝试 source `shunit2` 测试框架，但 `shunit2` 未安装在 CI runner 环境中。

### 与 PR 变更的关联
**与本次 PR 变更无关。** 本次 PR 仅新增了一个 Go 1.25.6 的 Dockerfile（`Others/go/1.25.6/24.03-lts-sp4/Dockerfile`）及对应的 README、image-info.yml、meta.yml 条目。Docker 镜像构建和推送均已成功完成（日志中 `#7` 至 `#11` 全部 DONE，`[Build] finished`、`[Push] finished`），失败发生在 CI 工具自身的测试基础设施层，属于 CI 环境问题。

日志中"Error lines"部分出现的 `#7 66.74 go/src/fmt/errors.go` 等行并非错误输出——它们是 `find ... -exec touch ...` 命令的正常文件列表输出，仅仅因为文件名包含 "error" 字符串被 CI 日志解析器误归为错误行。Docker 构建步骤 #7 明确标记为 `#7 DONE 67.8s`，构建成功。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架，确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能够正常 source 该工具。例如在 runner 初始化脚本中添加 `dnf install -y shunit2` 或通过包管理器安装对应包。

### 方向 2（置信度: 低）
检查 `eulerpublisher` 的 `common_funs.sh` 中 `shunit2` 的 source 路径是否正确，可能需要调整为 CI runner 上的实际安装路径。

## 需要进一步确认的点
- `shunit2` 在 openEuler 24.03-LTS-SP4 的 yum 仓库中对应的包名（可能是 `shunit2` 或其他名称）
- 其他同类镜像（如 `Others/go/1.25.6/24.03-lts-sp3/Dockerfile` 等）的 CI [Check] 阶段是否也遇到相同问题，以确认是否为该 runner 节点的个例还是系统性缺失
- 确认 CI runner 镜像模板中是否应预装 `shunit2`，或需在 CI pipeline 配置中新增安装步骤

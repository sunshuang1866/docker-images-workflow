# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试库缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-10 09:24:00,652-INFO: [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-CRITICAL: [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 测试环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 容器的 Check 阶段在执行 `common_funs.sh` 时尝试通过 `.` 命令加载 `shunit2` 测试框架库，但该库文件在 CI runner 环境中不存在，导致 Docker 镜像健康检查（[Check] 阶段）无法执行、直接失败。

### 与 PR 变更的关联
- **无关**。本次 PR 仅新增 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件及对应的元数据更新（meta.yml、README.md、image-info.yml）。
- Docker 镜像的编译（422/422 全部成功）、构建与推送阶段均已正常完成：
  - `meson compile -j -1 -C build` → 422/422 目标全部链接成功
  - `meson install -C build` → 所有二进制文件和 man page 安装到 `/usr`
  - Docker 镜像导出与推送 → `#13 DONE 36.0s`
- 失败仅发生在 CI 编排框架 `eulerpublisher` 的后置检查（[Check]）阶段，与本次 PR 的 Dockerfile、配置或元数据文件无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 测试框架包。需要在 CI 测试节点的基础镜像或预置脚本中安装 `shunit2`（如在 openEuler 上可通过 `dnf install shunit2` 或从源码部署）。这不是 PR 作者需要处理的代码问题。

### 方向 2（置信度: 低）
如果是 CI 编排脚本 `common_funs.sh` 的 `PATH` 或库搜索路径配置有误，导致已安装的 `shunit2` 未被找到，则需要 CI 维护者修正 `common_funs.sh` 中的 `shunit2` 加载路径。但鉴于 build/push 阶段均正常，此方向可能性较低。

## 需要进一步确认的点
- 该 [Check] 失败是仅出现在 aarch64 架构 runner，还是 x86_64 runner 也存在同样问题（日志仅展示了 aarch64 的构建输出，需要确认 x86_64 的日志状态）。
- `shunit2` 是否在 CI runner 镜像中有安装但被错误路径引用，还是确实从未安装过（需查看 CI runner 环境配置文件）。

## 修复验证要求
无需 code-fixer 执行验证。此失败为 CI 基础设施问题，不属于 PR 代码修改范畴。

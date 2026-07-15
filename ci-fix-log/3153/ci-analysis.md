# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11（YAML / 元数据文件错误，含 CI appstore 路径校验失败）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 11:27:51,489-...-INFO: Difference: [
    "README.md"
]

2026-07-14 11:28:17,839-...-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检阶段，`README.md` 文件的路径校验未通过。校验工具期望路径为 `/README.md`，但实际检测到该文件路径不满足 appstore 发布规范要求（可能是校验逻辑中路径归一化/前缀剥离导致不匹配，或检查规则近期调整所致）。

### 与 PR 变更的关联
PR 仅修改了仓库根目录下 `README.md` 和 `README.en.md` 的文档内容（更新基础镜像可用 tag 列表：将 `24.03-lts-sp2/latest` 改为 `24.03-lts-sp4/latest`，并新增 `24.03-lts-sp3`、`25.09`、`24.03-lts-sp2` 条目）。

PR 代码变更本身**内容正确**——它将曾错误指向 `openEuler-24.03-LTS-SP1/docker_img/` 的 `24.03-lts-sp2/latest` 链接修正为正确的 `openEuler-24.03-LTS-SP4/docker_img/`。失败原因是 CI appstore 路径校验器对根目录 `README.md` 的路径判定与预期不符，属于 CI 校验层面的问题，而非 PR 变更内容有问题。

## 修复方向

### 方向 1（置信度: 中）
CI appstore 校验工具 `eulerpublisher/update/container/app/update.py` 中的路径校验规则可能对仓库根目录文件（如 `/README.md`）存在误判。需要检查该校验逻辑：`README.md` 作为仓库根目录级文档文件，是否应当在 appstore 发布规范的"允许/豁免路径"列表中，还是校验器需要修正其路径归一化逻辑（例如 git diff 中的 `a/README.md` 前缀未被正确剥离）。

### 方向 2（置信度: 低）
若 CI 校验器是近期更新后引入了对根目录文件的检查（此前未对 README.md 做路径要求），则需要在校验配置中将根目录级 `README.md` 添加为例外项或预期路径白名单。

## 需要进一步确认的点
1. `eulerpublisher/update/container/app/update.py` 中路径校验逻辑的具体实现——它是如何判定一个文件路径"不符合 appstore 规范"的。
2. 根目录 `README.md` / `README.en.md` 在 appstore 发布规范中的预期角色：是否应被纳入 appstore 校验范围，还是应作为仓库级文档被豁免。
3. CI 日志来源实际是 `PR 3184`（分支 `fix/3153`），与上下文标注的 PR `#3153` 可能存在对应关系偏差——需确认本次分析的 CI 日志是否确实对应 PR #3153 的构建。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher` 工具代码（而非 PR 本身的 Dockerfile/文档），则属于 CI 工具链修复，code-fixer 需：
1. 确认 `update.py` 中路径校验函数的完整逻辑和错误触发条件。
2. 若为工具 bug，提交修复时需附带一个只修改根目录 README.md 的测试用例，验证修复后该用例通过校验。

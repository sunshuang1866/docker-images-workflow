# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI 校验覆盖过头
- 新模式症状关键词: Path Error, expected path, appstore, README.md, specification errors

## 根因分析

### 直接错误
```
2026-07-14 11:28:17,839-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

CI 差异检测结果显示仅一个文件变更：
```
Difference: [
    "README.md"
]
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: CI appstore 发布规范预检工具 `update.py` 对 PR 中的所有变更文件执行路径格式校验，仓库根目录的 `README.md` 不在任何镜像目录（如 `Bigdata/`、`AI/` 等）之下，不满足 appstore 镜像发布所需的路径结构规范，被判定为路径错误。

### 与 PR 变更的关联
**PR 变更与失败之间有触发关系，但无因果关系。** PR #3153 的改动完全合法——仅更新了仓库根目录下 `README.md` 和 `README.en.md` 中基础镜像可用 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 等条目）。CI 失败的原因是预检工具将"仓库根目录文档文件"错误地纳入了 appstore 镜像路径校验范围——该文件本身就不应属于任何镜像目录，预检工具的逻辑对纯文档类 PR 存在误判。

## 修复方向

### 方向 1（置信度: 中）
**该失败为 CI 基础设施行为问题，PR 代码变更无需修改。** 失败的真正原因不在 PR 变更内容中，而在于 CI 的 appstore 预检工具未能区分"仓库级文档变更"与"镜像发布变更"。需要由 CI 平台维护者调整 `update.py` 的检查逻辑：对仓库根目录的 `README.md`、`README.en.md` 等非镜像目录文件做豁免过滤，或仅在变更文件实际位于已知镜像场景目录下时才执行路径校验。

### 方向 2（置信度: 低）
若 CI 工具短期无法修改，可尝试在 PR 中额外附带一个合法的镜像目录变更（如更新某个已有镜像的 `meta.yml` 或 `image-info.yml`），使预检工具检测到至少一个合法路径并通过整体校验。但此方向仅为绕过 CI 限制的 workaround，不推荐作为正式方案。

## 需要进一步确认的点
1. 确认 `update.py` 中的路径校验逻辑是否对所有 `git diff` 输出的变更文件一律执行检查，还是存在白名单/排除列表。仓库根目录文件（`README.md`、`README.en.md`、`.gitignore` 等）是否理应被排除。
2. 确认是否存在其他类似案例（纯文档 PR 被 appstore 预检挡下），以判断这是特例还是已知的系统性问题。历史知识库模式 11 中 PR #2512 的多次 `.claude/README.md` 路径校验失败案例与本问题性质相似，但后者涉及的是 `.claude/` 工具目录内部路径不规范，有实际修正空间；而本 PR 的 `README.md` 位于仓库根目录，本身就不应属于任何镜像路径层级，性质不同。
3. 确认该 PR 是否可以通过其他 CI 流程（如跳过 appstore 检查的轻量 PR 流程）合入，或是否需要 CI 管理员手动 override 该检查。

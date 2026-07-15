# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-14 15:27:59,455-/home/jenkins/.../eulerpublisher/update/container/app/update.py[line:356]-INFO: Difference: [
    "README.md"
]
...
2026-07-14 15:28:07,685-/home/jenkins/.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范校验工具）
- 失败原因: PR 修改了根目录的 `README.md`，CI 的 appstore 发布规范检查器将此文件纳入校验范围，但该文件不在任何应用镜像目录（`{category}/{image}/{version}/{os-version}/`）下，导致路径校验失败。CI 提示期望路径为 `/README.md`，但根级 README.md 的实际路径可能在校验上下文中不匹配（如缺少特定目录层级前缀）。

### 与 PR 变更的关联
PR 仅修改了两个根级文档文件的镜像 Tag 列表：
- `README.md`：将 `latest` 指向从 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 独立条目
- `README.en.md`：同上

CI 在检测到变更文件 `README.md` 后，对其执行 appstore 发布规范校验，由于根级 README.md 不属于任何应用镜像发布目录，路径验证失败。**该失败并非由 PR 内容错误引起，而是 CI 规范检查器对纯文档 PR 的误判。**

## 修复方向

### 方向 1（置信度: 中）
这是一个 CI appstore 规范校验的误报——PR 本质是纯文档更新（修改 README 中支持的镜像 Tag 列表），不涉及任何应用镜像的发布。根级 `README.md` 不应被 appstore 发布规范校验器检查。修复方向：确保 CI 的规范检查器跳过根级文档文件（`/README.md`、`/README.en.md` 等），仅对应用镜像目录内的文件执行路径校验。

### 方向 2（置信度: 低）
如果 CI 确实要求任何修改 `README.md` 的 PR 都需满足某种路径规范，则需要确认 CI 校验器对根级 `README.md` 的期望路径格式究竟是什么（错误信息 `The expected path should be /README.md` 存在歧义——可能是指期望路径恰好就是根路径，但实际路径在克隆时的工作目录上下文中不匹配），然后调整校验器的路径比较逻辑。

## 需要进一步确认的点
- 错误信息 `[Path Error] The expected path should be /README.md` 中 `/README.md` 的确切含义：是期望路径为仓库根目录下的 `README.md`，还是期望路径以 `/README.md` 结尾的某个模式？需查阅 `update.py` 第 273 行附近的路径校验逻辑确认。
- CI 的 appstore 规范检查器是否有白名单机制可以跳过根级纯文档文件的校验；若有，需确认如何将 `/README.md` 和 `/README.en.md` 加入白名单。
- 历史上同类纯文档 PR 是否也曾触发此校验失败，以确认是否为 CI 工具的已知局限而非本次 PR 引入的新问题。

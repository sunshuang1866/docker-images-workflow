# 修复摘要

## 修复的问题
上游 pagure.io 归档 URL 失效导致 getdeps 下载到 HTML 页面而非 tar.gz 文件，构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile`: 修复 pre-copy 目标文件名中的拼写错误（`libaio-libaio-libaio` → `libaio-libaio`，与 getdeps 从 URL 提取的文件名一致）
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 新增 fetcher.py 补丁，在 `download()` 方法开头检查 `self.archive_file` 是否已存在且大于 10KB，如是则直接返回跳过下载

## 修复逻辑
CI 分析报告指出两个并发根因：
1. Dockerfile 中 `cp` 的目标文件名写成了 `libaio-libaio-libaio-0.3.113.tar.gz`（三个 "libaio"），但 getdeps 从下载 URL `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 提取的文件名是 `libaio-libaio-0.3.113.tar.gz`（两个 "libaio"），导致 getdeps 找不到预置文件而重新从已失效的上游下载
2. 即使文件名匹配，getdeps 的 fetcher 也可能无条件覆盖已存在的文件

修复方案（对应分析报告方向1）：
- 修正 Dockerfile 中的文件名拼写，使预拷贝文件能被 getdeps 识别
- 在 fetcher.py 的所有 `download()` 方法开头注入存在性检查：若目标文件已存在且大小超过 10KB（排除下载失败返回的 HTML 页面），直接返回文件路径，不触发网络下载

## 潜在风险
- `os.path.getsize` 检查阈值 10KB 为保守值，libaio 真实 tar.gz 远大于此，不会误判
- `download()` 补丁会影响所有 ArchiveFetcher 子类，如某类未定义 `self.archive_file` 属性将抛 AttributeError；但 Meta getdeps 的 fetcher 体系均使用该属性，风险低
- 若上游恢复后文件内容更新但文件名不变，预置的旧文件可能会被错误复用（因跳过了下载），但考虑到 libaio 版本固定（0.3.113），此场景不会发生
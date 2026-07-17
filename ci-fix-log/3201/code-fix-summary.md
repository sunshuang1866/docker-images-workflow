# 修复摘要

## 修复的问题
COPR 仓库下载超时导致 dnf install 失败，通过调优 dnf 超时/重试/速率参数提高下载容忍度。

## 修改的文件
- `AI/maca-sdk/3.7/24.03-lts-sp3/Dockerfile`: 在 `dnf makecache` 之前追加 dnf 配置，降低最低速率阈值（minrate=100）、延长超时（timeout=600）、增加重试次数（retries=10）、限制并行下载数（max_parallel_downloads=4），以适应 COPR 仓库对 aarch64 大包的缓慢下载速度。

## 修复逻辑
失败根因是第三方 COPR 仓库 `eur.openeuler.openatom.cn` 对大型 RPM 包（如 400MB 的 mcblaslt）下载速率极低（<1KB/s），触发 curl 的 30 秒低速超时。dnf 默认无显式 `minrate`/`timeout`/`retries` 配置，完全依赖 curl 内置默认值。通过 `/etc/dnf/dnf.conf` 设置 `minrate=100`（将最低速率阈值从 curl 默认的 1000 bytes/sec 降至 100）、`timeout=600`（将超时延长至 10 分钟）、`retries=10`（增加自动重试次数）、`max_parallel_downloads=4`（限制并发下载以避免带宽争抢），可显著提高在低带宽环境下的下载成功率。

## 潜在风险
- `minrate=100` 设置极低，即使仓库速率极慢也不会触发超时，但构建时间可能显著延长。
- `timeout=600` + `retries=10` 在最坏情况下单包可能等待 100 分钟。若 COPR 仓库完全不可达（而非仅慢），会导致 CI 超时。
- `max_parallel_downloads=4` 降低了并发度，在高速网络下反而会降低效率，但当前场景下可避免多连接争抢有限带宽。
- 此修复仅缓解下载层问题，若 COPR 仓库彻底宕机则无效。
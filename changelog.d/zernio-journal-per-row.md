---
bump: patch
title: Zernio journal writes only what changed
---
## vi
### Sửa lỗi
- Sổ giao nhận tin của Zernio giờ lưu từng dòng và chỉ ghi phần thay đổi, không ghi lại cả khối JSON mỗi lần có tin. Hội thoại nhàn rỗi và file khoá cũ được dọn.

## en
### Fixed
- The Zernio delivery journal now keeps one row per event, message and conversation and writes only the rows that changed, instead of rewriting one JSON cell on every webhook. Idle conversations and stale lock files are cleaned up.

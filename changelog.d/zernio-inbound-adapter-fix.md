---
bump: patch
title: Zernio inbound adapter rejects a bad message with 400 again
---
## vi
### Sửa lỗi
- Đường nhận tin nội bộ `/zernio/inbound` trả lại 400 khi tin thiếu trường, thay vì gặp lỗi chương trình.

## en
### Fixed
- The internal `/zernio/inbound` adapter returns 400 for a malformed message again instead of crashing.

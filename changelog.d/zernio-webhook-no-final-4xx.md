---
bump: patch
title: Zernio no longer drops customer messages while a bot restarts
---
## vi
### Sửa lỗi
- Tin khách gửi tới đúng lúc bot Zernio đang khởi động lại không còn bị Zernio bỏ hẳn. Javis báo Zernio gửi lại sau 30 giây thay vì từ chối.
- Đổi tên tài khoản Instagram của shop không còn làm mọi tin bị từ chối. Tin có chữ ký đúng nhưng thiếu trường được ghi nhận và bỏ qua, để Zernio không tự tắt webhook.

## en
### Fixed
- A customer message that arrives while a Zernio bot restarts is no longer dropped for good. Javis asks Zernio to resend it in 30 seconds instead of rejecting it.
- Renaming the shop's Instagram account no longer rejects every message. Signed events with missing fields are acknowledged and skipped, so Zernio does not switch the webhook off.

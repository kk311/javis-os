---
bump: patch
title: Zernio tells staff from the bot by sentVia and asks for message.sent in setup
---
## vi
### Sửa lỗi
- **Nhận ra tin nhân viên chắc hơn.** Tin Zernio đánh dấu gửi từ người (app Instagram, bảng Zernio) luôn là nhân viên, kể cả khi trùng chữ với câu mẫu của bot. Tin gửi qua API vẫn khớp theo ID rồi mới tới nội dung, nên tin của bot không bị nhận nhầm thành nhân viên.
- Form thiết lập Zernio hướng dẫn đăng ký cả `message.sent`; thiếu sự kiện này bot không biết nhân viên đã trả lời. Nhãn form không còn ghi riêng Instagram.

## en
### Fixed
- **Staff replies are recognised more reliably.** A message Zernio marks as sent by a person (Instagram app, Zernio dashboard) is always staff, even with the bot's exact words. API sends still match by id first and then by text, so the bot's own reply is never taken for staff.
- The Zernio setup form asks to register `message.sent` as well; without it the bot cannot tell that staff replied. Form labels no longer say Instagram only.

---
bump: patch
title: Zernio accounts follow their connection and recognise bot replies by id
---
## vi
### Sửa lỗi
- **Tài khoản Zernio đi theo kết nối.** Khóa API và webhook secret lưu một lần ở kết nối, tài khoản chỉ giữ `connection_id`, nên đổi khóa ở kết nối là mọi tài khoản dùng ngay.
- **Nhận ra tin của bot theo ID, không so chữ.** Nhân viên gõ đúng câu mẫu của bot vẫn được tính là nhân viên và bot tạm dừng.
- Thông báo chuông khi gửi lỗi theo ngôn ngữ đang dùng.

## en
### Fixed
- **Zernio accounts follow their connection.** The API key and webhook secret live once in the connection; an account keeps only its `connection_id`, so rotating a key there reaches every account.
- **Bot replies are recognised by message id, not by wording.** Staff typing the bot's exact template still counts as staff and pauses the bot.
- The bell note for a failed send follows the interface language.

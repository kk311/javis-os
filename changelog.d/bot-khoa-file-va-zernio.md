---
bump: minor
title: A customer-facing bot no longer gets the vault file tools or the Zernio inbox tools
---
## vi
### Bảo mật
- **Bot trả lời khách không còn công cụ đọc file trong brain và công cụ hộp thư `zernio_*`.** Ở mức "Được ghi", bot từng nhận các công cụ này, nên một người lạ nhắn tới có thể dụ bot đọc ghi chú hoặc hội thoại của khách khác. Phiên của chủ không đổi. Bot cần tài liệu thì dùng mức "Đọc tài liệu" hoặc phần tra tài liệu trước mỗi lượt.

## en
### Security
- **A customer-facing bot no longer gets the vault file tools or the `zernio_*` inbox tools.** At the "can write" level a bot used to receive them, so a stranger could talk it into reading notes or other customers' chats. The owner's own sessions are unchanged. A bot that needs documents uses the "Reads documents" level or the pre-turn document search.

---
bump: minor
title: Zernio hands chats to staff on its own and switches AI back on after staff reply
---
## vi
### Thay đổi
- Khách gửi ảnh, file hoặc bot báo cần người thì hội thoại tự chuyển sang nhân viên, bot im lặng. Nhân viên nhắn khách thì AI tự bật lại, chỉ trả lời tiếp khi đã qua 5 phút kể từ tin cuối của nhân viên.
- Bỏ mục Sự cố gửi tin trong Hội thoại. Tin bot không gửi được sẽ báo vào chuông, mỗi lần gửi lỗi chỉ báo một lần.

## en
### Changed
- When a customer sends a photo or file, or the bot asks for a person, the chat moves to staff and the bot stays quiet. Once staff message the customer, AI switches back on and only replies again 5 minutes after the last staff message.
- The Delivery issues panel in the inbox is gone. Replies the bot cannot send are reported to the bell, once per failed send.

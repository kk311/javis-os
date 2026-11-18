---
bump: minor
title: Zernio records staff replies, pauses the bot after them and shows Instagram media
---
## vi
### Thêm mới
- Kênh Zernio nhận sự kiện `message.sent`: tin shop trả lời khách (app Instagram, Zernio, Hội thoại Javis) được ghi vào Hội thoại dưới tên Nhân viên; tin tự động của Zernio ghi là Tự động Zernio.
- Nhân viên vừa trả lời thì bot im 5 phút. Tin khách gửi trước đó coi như đã được trả lời; tin khách gửi trong lúc chờ sẽ được bot trả lời nếu hết 5 phút mà nhân viên chưa trả lời tiếp.
- Hội thoại hiện ảnh, bài đăng kèm caption, story và reel khách gửi qua Instagram bằng link gốc, không tải về máy.

### Sửa lỗi
- Tin Instagram chỉ có ảnh hoặc bài chia sẻ không còn hiện thành ô trống.

## en
### Added
- The Zernio channel handles `message.sent`: replies the shop sends (Instagram app, Zernio, the Javis inbox) are stored in the inbox as staff; Zernio automations are stored as such.
- After a staff reply the bot stays quiet for 5 minutes. Earlier customer messages count as answered; messages sent during the pause are answered by the bot if staff has not replied again when it ends.
- The inbox shows Instagram photos, shared posts with caption, stories and reels by their original link, without downloading them.

### Fixed
- An Instagram message with only a photo or shared post no longer shows as an empty bubble.

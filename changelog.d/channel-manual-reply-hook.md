---
bump: minor
title: Channels can prepare the inbox draft from customer photos
---
## vi
### Thêm mới
- **Kênh tự chuẩn bị lượt soạn trả lời.** Khi bấm Javis soạn, một kênh (kể cả kênh từ gói Store) có thể tự đọc ảnh khách gửi và đưa mô tả cho bot, nên tin chỉ có ảnh không còn báo "chưa có tin khách". Lõi không đọc ảnh lần hai. Kênh từ chối thì anh thấy đúng lý do kênh đưa. Kênh không khai điểm này chạy y như cũ.

## en
### Added
- **Channels can prepare the inbox draft.** When the owner asks the A.I. to draft a reply, a channel (including one from a Store pack) can read the customer's photos itself and hand the bot a description, so a photo-only message no longer says "no customer message". The core does not read the photo a second time. If the channel refuses, the owner sees the channel's own reason. Channels without this hook work exactly as before.

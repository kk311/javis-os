---
bump: minor
title: Store packs can add inbox channels
---
## vi
### Thêm mới
- **Gói Store thêm được kênh hộp thư.** Gói khai `provides.channels: [channels/<tên>.py]` là kênh mới hiện ở trang Chatbot và Hội thoại, kèm logo riêng, không phải sửa mã lõi. Kênh chỉ nạp khi gói đang bật và mã khớp lúc anh đồng ý cài; gói không bao giờ thay được kênh có sẵn.
- **Kênh của gói tự khai form nhập tài khoản.** Thay một ô token, kênh khai các ô cần nhập (chữ, mật khẩu, danh sách chọn tải từ route của chính gói). Khoá API gõ vào không bao giờ nằm trên URL; sửa tài khoản mà không động vào ô nào thì giữ nguyên thông tin cũ.

## en
### Added
- **Store packs can add inbox channels.** A pack listing `provides.channels: [channels/<name>.py]` adds a channel to the Chatbot and Conversations pages, with its own logo, without core edits. It loads only while the pack is enabled and its code matches what the owner agreed to install; a pack can never replace a built-in channel.
- **Pack channels declare their own account form.** Instead of a single token box, a channel lists its fields (text, password, or a select loaded from the pack's own route). A typed API key never goes into a URL, and editing an account without touching any field keeps the saved credentials.

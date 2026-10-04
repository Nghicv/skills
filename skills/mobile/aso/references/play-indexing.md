# How Google Play indexes metadata

> **Đừng áp luật iOS sang đây.** Nhiều quy tắc **ngược hẳn** — xem bảng đối lập bên dưới
> trước khi làm bất cứ việc gì. Sai chỗ này là làm hỏng listing.

## Đối lập với iOS

| | iOS | Google Play |
|---|---|---|
| Field keyword riêng | 100 ký tự | **không có** |
| Description | không index | **4000 ký tự, CÓ index** |
| Lặp từ | vô ích, đốt ký tự | **cần** — nhưng có chừng mực, xem dưới |
| Review người dùng | không phải tín hiệu xếp hạng | **là tín hiệu** |
| A/B test chữ | PPO không test được | **test được** qua Store listing experiments |
| Đo rank | API công khai, sâu tới 200 | scrape, chỉ tới ~30 |

## Field limits `[GOOGLE]`

| Field | Limit | Index? | Trọng số |
|---|---|---|---|
| Title | 30 | Có | **mạnh nhất** |
| Short description | 80 | Có | **cao** — cao hơn long description |
| Long description | 4000 | Có | trung bình |
| Developer name | — | Có | thấp |

Không có field keyword. Toàn bộ relevance đến từ ba ô trên cộng tín hiệu hành vi.

## Mật độ từ khoá `[FOLKLORE]`

Google dùng NLP ngữ nghĩa, không đếm từ thô. Thực hành hiện tại:

- Khoảng **một lần khớp chính xác cho mỗi ~250 ký tự** description
- Viết cho người đọc, không nhồi. **Nhồi từ khoá bị phạt.**
- Ưu tiên đưa từ mạnh nhất vào Title, rồi Short description, rồi mới rải biến thể tự
  nhiên trong Long description

Đây là khác biệt lớn nhất so với iOS: iOS đếm *từ duy nhất*, Play đọc *văn bản tự nhiên*.

## Short description là đòn bẩy bị xem nhẹ `[FOLKLORE]`

80 ký tự nhưng trọng số cao hơn hẳn long description, và nó cũng là thứ người dùng đọc
đầu tiên — vừa là đòn bẩy rank vừa là đòn bẩy conversion. Nếu chỉ sửa được một ô, sửa ô này.

## Tín hiệu ngoài văn bản `[FOLKLORE]`

Play tính cả những thứ iOS không tính (hoặc tính ít hơn):

- Rating và **nội dung review** (từ khoá trong review có tác dụng)
- Lượt cài, tỉ lệ gỡ cài, retention
- Độ ổn định (ANR / crash rate trong Android vitals)

Nghĩa là chất lượng app ảnh hưởng rank trực tiếp hơn so với iOS. Không sửa được bằng chữ.

## Store listing experiments `[GOOGLE]`

A/B test ngay trong Play Console, **test được cả text** (title, short/long description) lẫn
đồ hoạ — thứ Apple PPO không làm được.

- Chạy được ở cấp mặc định (global) hoặc cấp từng locale
- Cần lưu lượng đủ, giống PPO: app nhỏ sẽ mất nhiều tuần
- Đọc `screenshots-ppo.md` cho kỷ luật chung về đọc kết quả A/B

## Custom store listings

Play cho tạo listing riêng theo nguồn traffic / quốc gia / chiến dịch. Không ảnh hưởng
organic rank nhưng là công cụ conversion mạnh cho quảng cáo trả tiền.

## Chuyển keyword từ iOS sang Android

Cùng một app thì **chiến lược** giống nhau, **danh sách** thì không. Khác biệt bị ép bởi
cấu trúc field, không phải do tuỳ hứng.

| | iOS | Android |
|---|---|---|
| Đơn vị | **từ rời** — ~15 token cho 100 ký tự | **cụm** — 3-5 cụm trọng tâm, viết thành văn |
| Ghép cụm | Apple tự ghép giữa các field | phải tự viết ra câu |
| Lặp | cấm | cần, có chừng mực |

```
iOS keywords:  budget,expense,spending,track,money,saving,bill,finance
               → Apple tự ghép "budget tracker", "expense tracker"...

Android short_description (80):
   "Track your budget and expenses - simple spending tracker for daily money"
               → không ai ghép hộ, phải viết đủ cụm
```

**Quy trình:** lấy nhóm CORE của iOS → chọn 1 cụm cho Title, 1-2 cụm cho short_description
→ rải biến thể tự nhiên trong full_description (~1 lần khớp/250 ký tự).

**Ba lý do danh sách lệch thật:**
- Tập đối thủ khác — không phải app nào cũng ship cả hai store
- Nhân khẩu khác — VN/ID/BR/IN tỉ trọng Android cao hơn, cách gõ tìm kiếm bình dân hơn
- Volume phân bố khác giữa hai store

## Giữ chung một file, tách bằng cờ

Mặc định mọi keyword là `platform: both`. Chỉ tách khi có **bằng chứng**: rank lệch nhiều,
tập đối thủ khác, hoặc cụm chỉ hợp format một store.

Lý do giữ chung `keywords.yml` + `rank-history.csv`: khi một keyword mạnh ở nền tảng này mà
mất hút ở nền tảng kia, đó là **tín hiệu, không phải nhiễu** — gần như luôn có nghĩa listing
bên kia chưa nhắc tới nó. Tách đôi file thì không bao giờ phát hiện ra.

## Sources

Cộng đồng/thứ cấp, không phải tài liệu Google:
- https://www.applaunchflow.com/blog/google-play-store-optimization-2026
- https://asomobile.net/en/blog/app-listings-in-google-play-2026/
- https://www.whixframe.com/blog/google-play-short-description-guide

# Deploy VetLens PWA trên Render

Bản web/PWA dùng cùng mô hình và nội dung tư vấn hiện tại. iPhone cài qua Safari → Chia sẻ → Thêm vào Màn hình chính. Trang `/install` hướng dẫn chi tiết. Không có file APK cho iOS; phân tích và lịch sử cần kết nối tới server. Service worker chỉ cache trang hướng dẫn, tài nguyên công khai và trang mất kết nối; không cache API, ảnh người dùng hay hội thoại.

## Cách triển khai

1. Dùng `dist/vetlens-render.zip`, giải nén vào một repo GitHub mới, để `render.yaml` ở gốc repo. Gói này chứa code web và đúng bốn checkpoint đang dùng; không chứa dữ liệu huấn luyện, ảnh người dùng, lịch sử hoặc APK.
2. Commit và push bằng Git trên máy tính. Không upload mô hình qua giao diện web GitHub vì giới hạn kích thước upload từng file. Không copy `.gitignore` của dự án gốc vào repo này vì nó đang loại toàn bộ thư mục `models/`.
3. Render → New → Blueprint → chọn repo → kiểm tra cấu hình rồi deploy. Blueprint chọn gói `standard` và ổ đĩa persistent 1 GB, có phí theo giá Render tại thời điểm triển khai. Chọn cấu hình RAM đủ cho PyTorch và bốn mô hình; chưa đo tải production trên Render. Không tự đổi sang gói RAM thấp khi chưa kiểm tra bộ nhớ.
4. Build cài PyTorch CPU, dependency web, rồi kiểm tra đủ checkpoint. Start chạy một worker Uvicorn trên `$PORT`. Health check: `/healthz`.
5. Mở URL HTTPS Render cấp, kiểm tra `/api/models`: cả bốn mục phải có `available: true`. Upload ảnh thử thực tế cho từng loài trước khi chia sẻ URL.
6. Chia sẻ `https://TEN-DICH-VU.onrender.com/install` cho người dùng iPhone. Không dùng localhost trên điện thoại. HTTPS là điều kiện để service worker hoạt động ngoài máy phát triển.

Nếu deploy từ repo dự án gốc thay vì gói riêng, cần đưa đúng các đường dẫn `web_checkpoint` trong `models_catalog.json` lên repo (có thể dùng `git add -f` cho từng file). Script build sẽ dừng nếu thiếu mô hình. Không cần đưa toàn bộ `data/`, `.venv/`, Android hoặc dataset lên Render.

## Dữ liệu và cập nhật

- `VETLENS_STATE_DIR=/var/data/vetlens` đặt SQLite trên persistent disk. Không dùng nhiều replica hoặc nhiều service chung file SQLite.
- Nếu tự chọn gói không có persistent disk, lịch sử có thể mất khi restart/redeploy. Cookie cũ không khôi phục được dữ liệu server đã mất.
- Chưa có đăng nhập: lịch sử gắn với cookie. Safari và PWA có thể dùng phiên khác nhau, chưa có đồng bộ giữa thiết bị.
- Khi thay tài nguyên cache, tăng tên CACHE trong `web/static/sw.js`. Service worker mới được kích hoạt khi các cửa sổ cũ đóng; mở lại ứng dụng để nhận bản mới.
- iPhone HEIC: backend hiện chưa hỗ trợ giải mã HEIC trực tiếp; nếu trình duyệt không chuyển đổi ảnh, dùng ảnh JPEG/PNG hoặc ảnh chụp màn hình. Không coi PWA là đã hỗ trợ mọi định dạng thư viện iPhone.
- Sau deploy, thử cài thật trên iPhone, thử mất mạng rồi kết nối lại, và kiểm tra lịch sử sau restart. Kiểm tra trình duyệt desktop không thay thế nghiệm thu trên iOS thật.

## Chạy local

Chạy `.\start_web.ps1`, truy cập `http://127.0.0.1:8000/install`. Tạo lại gói deploy bằng `.\.venv\Scripts\python.exe scripts/package_render.py`. Cấu hình Render và gói đã chuẩn bị; chưa được tự động deploy lên tài khoản Render.

# VetLens – web thử nghiệm

Web hỗ trợ bò, lợn và gà. Gà có hai nhánh: ảnh phân và ảnh toàn thân/vùng bệnh.
Chức năng chẩn đoán chó đã được loại khỏi API và giao diện.

## Chạy và triển khai

Python 3.12: cài requirements-render.txt rồi chạy
`uvicorn web.app:app --host 0.0.0.0 --port 8000 --workers 1`.
Render dùng render.yaml; build kiểm tra đủ cả bốn checkpoint, kể cả gà toàn thân.
`/healthz` kiểm tra tiến trình; `/api/models` kiểm tra nhánh mô hình sẵn có.
Kho chính: https://github.com/aichandoanbenh-oss/aichandoanbenh
Web: https://aichandoanbenh.onrender.com

## Bản mô hình hiện tại

Xem release.json để đối chiếu checkpoint và SHA256. Bò/gà phân dùng ResNet18;
lợn/gà toàn thân dùng EfficientNet-B0. Nhãn toàn thân gà chỉ là nhóm dấu hiệu.
Web xử lý trên máy chủ bằng ONNX Runtime CPU, cùng trọng số FP32 và cách
resize/chuẩn hóa ảnh của bản PyTorch; PWA không tự suy luận ngoại tuyến.
Chỉ giữ một mô hình trong RAM, chỉ giải mã/phân tích một ảnh mỗi lúc.
Yêu cầu phân tích đến khi đang bận nhận 503 kèm Retry-After: 5.

Kiểm tra local ngày 15/11/2026: 151/151 ảnh giữ nguyên nhãn dự đoán so với
PyTorch, sai lệch xác suất tối đa 0,000004. Peak working set trên Windows
284,32 MiB; đây không phải số đo RAM trên Render/Linux hoặc độ chính xác 100%.
Sau deploy cần kiểm tra Memory và ảnh lớn trên chính instance Render 512 MB.

Đây là bản thử nghiệm round3, chưa đạt mục tiêu 80% trên bộ ảnh ngoài của APK:
53/70 (75,7%); bộ cũ 64/81. Đây là tham chiếu kiểm thử APK, không phải kiểm định
độ chính xác chẩn đoán lâm sàng hoặc đo trực tiếp web Render.

Kho không chứa ảnh huấn luyện gốc, ảnh người dùng, lịch sử, APK hoặc thông tin bí mật.
Thành phần gà toàn thân có nguồn và nghĩa vụ AGPL-3.0: đọc BODY_NOTICE.md và
licenses/chicken_body/AGPL-3.0.txt. Mã train và manifest tương ứng nằm trong
scripts/ và training_sources/; không suy ra ảnh nguồn được tự do phân phối.

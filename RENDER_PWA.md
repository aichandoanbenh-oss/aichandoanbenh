# Triển khai VetLens trên Render

Repo GitHub aichandoanbenh-oss/aichandoanbenh, nhánh main; cấu hình render.yaml.
Render Blueprint cần chọn repo/nhánh này. Auto-Deploy phụ thuộc thiết lập dịch vụ.
Tệp cấu hình hiện dùng Standard và persistent disk, có phí theo tài khoản Render.

Build: pip install -r requirements-render.txt && python scripts/check_render_models.py
Start: uvicorn web.app:app --host 0.0.0.0 --port $PORT --workers 1
Health: /healthz. Lịch sử: VETLENS_STATE_DIR=/var/data/vetlens.
Không ghi đè/xóa ổ lịch sử khi cập nhật mã. Không đưa dữ liệu lịch sử lên GitHub.

Sau deploy, GET /api/models phải chỉ có cattle, pig, chicken và chicken.body_available=true.
Kiểm tra thật cả bốn nhánh và sự phân biệt input_type=fecal/body.
PWA cài qua /install vẫn cần máy chủ cho suy luận ảnh; không tương đương APK ONNX.
Đọc BODY_NOTICE.md trước khi triển khai thành phần gà toàn thân.

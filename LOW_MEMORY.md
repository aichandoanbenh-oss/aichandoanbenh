# Bản tối ưu bộ nhớ Render — 15/11/2026

Render Events đã xác nhận tiến trình cũ vượt RAM 512 MB. Bản sửa dùng ONNX
Runtime CPU thay PyTorch/torchvision trong tiến trình web. Bốn file ONNX FP32
lấy từ bản export đã kiểm tra của round3, kiểm tra SHA256 trong build.
Không lượng tử hóa, không train lại và không sửa ảnh/nhãn test.

- Cache một mô hình; giải phóng mô hình cũ trước khi nạp mô hình khác.
- Một luồng inference, tắt CPU arena và memory pattern của ONNX Runtime.
- Khóa từ trước giải mã ảnh đến khi lưu kết quả; yêu cầu phân tích khác nhận
  HTTP 503 với Retry-After: 5. Người dùng giữ ảnh và thử lại sau.
- Không sao chép ảnh đầy đủ để tạo thumbnail; không đọc BLOB ảnh khi liệt kê lịch sử.
- Không đổi gói Render hoặc cấu hình thanh toán. Giữ một worker Uvicorn.

## Kiểm tra đã thực hiện

`verify_low_memory_render.py --baseline` và `verify_low_memory_render.py` chạy
ở hai tiến trình tách biệt. 151 ảnh gốc được kiểm tra hash; đủ bốn nhánh qua
API local. 151/151 nhãn dự đoán giống PyTorch, không có nghĩa tất cả nhãn đúng.
Sai lệch xác suất lớn nhất: 0.0000039637088775634766.
Peak working set Windows: 284.32 MiB. Không import torch trong tiến trình mới.
Đã kiểm tra từ chối xử lý đồng thời, quyền truy cập khác phiên, đọc lịch sử và xóa chat.

Số đo Windows không thay thế RAM container Linux, không chứng minh mọi ảnh
đến giới hạn 20 megapixel đều chạy dưới 512 MB. Cần xác nhận live sau deploy.

## Sau khi được duyệt cập nhật

1. Push checkout `dist/render-repo` để Render cài requirements-render.txt mới.
2. Xác nhận build không cài PyTorch/torchvision; check_render_models.py kiểm tra bốn ONNX.
3. Kiểm tra healthz và bốn nhánh bằng ảnh gốc, đặc biệt ảnh phân gà 2,2 MB.
4. Theo dõi Memory/Events khi đổi nhánh, gửi ảnh lớn và nhiều yêu cầu.
5. Chỉ chạy lại đủ 151 ảnh khi lượt kiểm tra nhỏ ổn định; giữ riêng kết quả mới.

Render Free có thể mất lịch sử khi restart/redeploy vì không có persistent disk.
Bản sửa không thể khôi phục hội thoại đã mất. Không bật tự gửi lại POST để tránh
lưu trùng kết quả khi yêu cầu trước đã xử lý nhưng phản hồi bị mất.

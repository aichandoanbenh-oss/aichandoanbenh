# Cài đặt và chạy VetLens trên Windows

## 1. Cài thư viện bằng một lần nhấp

Nhấp đúp **setup.bat** tại thư mục gốc. Cần Internet và Windows 64-bit. Script tìm Python 3.12; nếu thiếu sẽ tải Python 3.12.10 từ python.org, kiểm tra chữ ký rồi cài cho người dùng hiện tại. Sau đó tạo `.venv`, cài thư viện web/train/xuất ONNX/báo cáo Word/kiểm thử trình duyệt và Chromium của Playwright.

Mặc định tự chọn PyTorch CUDA 12.4 nếu `nvidia-smi` nhận GPU NVIDIA, nếu không dùng CPU. Không cần kích hoạt venv thủ công. Thư viện được cài trong `.venv`; Python và cache trình duyệt được cài cho tài khoản Windows. Có thể chạy lại khi cài bị gián đoạn. Chỉ khi hiện **SETUP COMPLETE** mới coi là cài xong; xem lỗi trong `reports/setup-latest.log`.

Các tùy chọn trong PowerShell:

```powershell
.\setup.bat -Device CPU
.\setup.bat -Device CUDA
.\setup.bat -SkipBrowser
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_project.ps1 -CheckOnly
```

Nếu `.venv` có Python khác 3.12, đổi tên thư mục đó để giữ bản cũ rồi chạy setup lại. CUDA cần driver NVIDIA phù hợp; script không cài driver. Chế độ CPU chạy web và trainer gốc, nhưng các script sửa lợn gọi `.cuda()` trực tiếp và cần GPU NVIDIA.

**Setup chỉ cài thư viện Python và trình duyệt kiểm thử.** Không tự tải dataset, trọng số AI, Android SDK/JDK/Gradle hoặc chạy train. Cần giữ các file `models/`, `models_catalog.json`, `web/`; để train còn cần đầy đủ `data/processed`, ảnh gốc và manifest trong `reports/`. Repo Render không chứa đủ dữ liệu để train lại.

## 2. Mở web

Nhấp đúp **run_web.bat**, giữ cửa sổ chạy, rồi mở **http://127.0.0.1:8000**. Dừng bằng Ctrl+C.

Lệnh tương đương, chạy tại thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Nếu cổng 8000 đang dùng, đổi sang `--port 8001` và mở URL cùng cổng. Trang hướng dẫn PWA: `/install`; xem loài có checkpoint: `/api/models`. PWA cần mạng để phân tích; APK Android chạy offline. Deploy Render theo `RENDER_PWA.md`, không dùng setup Windows trên Render.

## 3. Train bản ResNet18 gốc

Sao lưu checkpoint, manifest và báo cáo trước khi train. Các script có thể ghi đè đầu ra; cài thư viện xong không có nghĩa đã đủ dataset.

Khi có sẵn `data/processed/{species}_experimental/manifest.json`, `summary.json` và ảnh mà manifest trỏ tới:

```powershell
.\.venv\Scripts\python.exe scripts/train_available.py --species dog --epochs 12 --reuse-prepared
.\.venv\Scripts\python.exe scripts/train_available.py --species cattle chicken pig --epochs 12 --reuse-prepared
```

Nếu muốn thực hiện lại bước chuẩn bị dữ liệu từ báo cáo nguồn, bỏ `--reuse-prepared`. Việc này chia lại tập và ghi đè manifest, chỉ thực hiện khi có đủ nguồn và đã lưu phiên bản cũ.

Đầu ra: `models/{species}_experimental_resnet18/best.pt`, `metrics.json`, `test_predictions.json`. Đây là nhánh gốc; không tự thay checkpoint web đang dùng. Tham số `--species` chỉ nhận `dog`, `cattle`, `chicken`, `pig`.

## 4. Train nhánh web có unknown

```powershell
.\.venv\Scripts\python.exe scripts/train_web_models.py
```

Script train cả bốn loài, không có `--species`. Cần manifest gốc của cả bốn loài và `data/processed/dog_oral_signs_candidates/manifest.json`, cùng ảnh tương ứng. Đầu ra: `models/{species}_web_experimental_resnet18/`.

Lợn đang triển khai là **EfficientNet-B0 v4**, không phải ResNet18 tạo bởi lệnh trên. **Không chạy `register_web_models.py` cũ sau đó**, vì nó sẽ trỏ lợn về checkpoint cũ. Chỉ cập nhật entry cần thiết trong `models_catalog.json` sau khi đánh giá đạt.

## 5. Tái tạo nhánh sửa lợn

Các script này yêu cầu CUDA, manifest web, checkpoint và các báo cáo/ảnh phát triển được chỉ định trong source. Đọc `BAO_CAO/Bao_cao_1_Huan_luyen_va_cau_hinh.docx` trước khi chạy; chúng không tự tìm và tải đủ dữ liệu.

```powershell
# Giai đoạn EfficientNet đầu; script này cũng train một candidate chó
.\.venv\Scripts\python.exe scripts/train_repair_round2.py
# Fine-tune cuối: tên script round3 nhưng đầu ra là pig_repair_v4
.\.venv\Scripts\python.exe scripts/train_pig_round3.py
.\.venv\Scripts\python.exe scripts/final_repair_audit.py
```

Đầu ra cuối: `models/pig_repair_v4_efficientnet_b0/best.pt`. Vòng cuối cần `reports/external_audit/atlas_holdout.json`, `pig_manifest.json`, các ảnh được trỏ tới và checkpoint `models/pig_repair_efficientnet_b0/best.pt`. Chọn model bằng validation; ảnh test đã dùng để điều chỉnh không còn là kiểm định độc lập.

## 6. Đưa mô hình mới vào web / Android

1. Đánh giá candidate, lưu phiên bản cũ và sửa `web_checkpoint`, `web_labels_vi` tương ứng trong `models_catalog.json`. Thứ tự lớp phải khớp checkpoint.
2. Restart web để nạp trọng số mới; thay file khi server đang chạy không tự xóa cache mô hình.
3. Nếu thay model Android, xuất lại ONNX trước khi build. Export cần `test_predictions.json` cạnh checkpoint và các ảnh đối chiếu còn tồn tại.

```powershell
.\.venv\Scripts\python.exe scripts/export_android_models.py
.\build_apk.ps1
```

Build APK cần JDK 17, Android SDK 35, Gradle 8.9. `build_apk.ps1` hiện dùng công cụ trong `data/android_tools` và cấu hình SDK local của dự án; setup.bat không cài bộ công cụ Android. Đầu ra **dist/apknews.apk**. Nếu chỉ sửa tư vấn:

```powershell
.\.venv\Scripts\python.exe scripts/sync_care_content.py
.\build_apk.ps1
```

## 7. Kiểm tra và tạo báo cáo

```powershell
# Web phải đang chạy ở cổng 8000
.\.venv\Scripts\python.exe scripts/test_web.py
.\.venv\Scripts\python.exe scripts/test_web_new_classes.py
# Các bài dưới hiện dùng cổng 8001
.\.venv\Scripts\python.exe scripts/test_dashboard.py
.\.venv\Scripts\python.exe scripts/test_pwa.py
# Báo cáo Word gốc: ghi lại cả hai file, cần model/dữ liệu thực nghiệm
.\.venv\Scripts\python.exe scripts/create_training_guides.py
# Bổ sung báo cáo 1 từ bản lưu trước đó, cần source và ảnh/báo cáo kèm theo
.\.venv\Scripts\python.exe scripts/enrich_training_report.py
```

Các script chụp hiện có gọi Microsoft Edge (`channel='msedge'`): máy cần cài Edge, hoặc sửa sang Chromium mà setup tải về bằng cách bỏ `channel='msedge'`. Không chạy lại bộ test có kỳ vọng bố cục cũ để đánh giá giao diện mới nếu chưa cập nhật test.

## 8. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| ModuleNotFoundError | Chạy setup.bat lại; dùng đúng `.venv\Scripts\python.exe`. |
| CUDA unavailable | Kiểm tra driver NVIDIA, `nvidia-smi`; dùng `-Device CPU` cho web nếu không có GPU phù hợp. |
| Thiếu checkpoint | Khôi phục đúng file theo `models_catalog.json`; pip không tải model của dự án. |
| Không tìm thấy ảnh/manifest | Khôi phục dataset tại đúng đường dẫn; repo deploy không chứa dataset train. |
| Cổng đang sử dụng | Mở server đang chạy hoặc chọn cổng khác; không chạy hai server cùng cổng. |
| Pip tải thất bại | Kiểm tra Internet/dung lượng ổ đĩa, đọc log, chạy lại setup. Không hiện thành công nếu còn lỗi. |
| Build Android lỗi SDK/JDK | Kiểm tra `data/android_tools`, `JAVA_HOME` và `android/local.properties`. |

Không có lệnh nào trong setup tự push Git, deploy Render hoặc train lại mô hình.

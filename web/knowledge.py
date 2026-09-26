"""Educational summaries, not prescriptions or confirmed diagnoses."""
from .care_guidance import guidance
from .medication_guidance import medication
GENERAL = 'Theo dõi ăn uống, thân nhiệt và thời điểm xuất hiện triệu chứng; chụp rõ vùng tổn thương và liên hệ thú y để khám, lấy mẫu khi cần. Không tự chọn kháng sinh hoặc liều thuốc từ kết quả ảnh.'
DATA = {
 'Dermatitis': ('Da đỏ, ngứa, rụng lông, có thể đóng vảy hoặc rỉ dịch.', 'Viêm da là nhóm biểu hiện rộng: ký sinh trùng, nhiễm khuẩn, nấm hoặc dị ứng đều có thể gây ra.', 'Ngăn gãi/liếm quá mức, giữ vùng da sạch và khô; thú y cần tìm nguyên nhân trước khi chọn thuốc.'),
 'Fungal_infections': ('Rụng lông, bong vảy, vùng da đỏ; hình dạng tổn thương thay đổi.', 'Nhãn nhiễm nấm rộng trong dữ liệu, có thể chồng lấn với nhãn ringworm.', 'Hạn chế tiếp xúc trực tiếp vùng da bệnh, vệ sinh đồ dùng; cần xét nghiệm nấm trước khi điều trị đặc hiệu.'),
 'ringworm': ('Mảng rụng lông, bong vảy, đôi khi hình tròn; có thể lây sang người.', 'Nấm dermatophyte; chỉ nhìn ảnh không xác định được tác nhân.', 'Vệ sinh môi trường và đồ dùng, rửa tay sau tiếp xúc; thú y cân nhắc thuốc kháng nấm sau khi xác nhận.'),
 'Hypersensitivity': ('Ngứa, da đỏ, liếm chân hoặc viêm tai tái diễn.', 'Có thể liên quan bọ chét, thức ăn hoặc dị nguyên môi trường; cần loại trừ ký sinh trùng và nhiễm trùng.', 'Ghi lại thức ăn, sản phẩm mới và thời điểm ngứa; trao đổi với thú y về kiểm soát bọ chét và khảo sát dị ứng.'),
 'demodicosis': ('Rụng lông từng mảng, đỏ da, đóng vảy; ca nặng có thể nhiễm khuẩn thứ phát.', 'Mạt Demodex tăng sinh, thường liên quan cơ địa hoặc bệnh nền.', 'Cần cạo da/xét nghiệm và đánh giá bệnh nền. Thuốc diệt mạt cần được thú y lựa chọn theo tuổi, cân nặng và tình trạng con vật.'),
 'foot_and_mouth': ('Sốt, chảy nhiều nước dãi, mụn nước hoặc loét miệng, tổn thương chân và đi khập khiễng.', 'Virus lở mồm long móng; nhiều nguyên nhân khác cũng gây loét và đi khập khiễng.', 'Nếu nghi ngờ, cách ly, hạn chế vận chuyển và liên hệ thú y địa phương ngay. Chăm sóc hỗ trợ và kiểm soát ổ dịch theo hướng dẫn thú y.'),
 'lumpy_skin': ('Các nốt sần trên da, sốt, giảm ăn hoặc giảm sữa; có thể sưng hạch.', 'Virus gây viêm da nổi cục ở trâu bò, thường truyền qua côn trùng hút máu.', 'Cách ly con nghi bệnh, kiểm soát côn trùng và liên hệ thú y. Không có thuốc đặc hiệu để tự điều trị từ ảnh; phòng bệnh bằng vaccine theo hướng dẫn địa phương.'),
 'mastitis': ('Bầu vú nóng, sưng, đau; sữa có cặn hoặc thay đổi màu, đôi khi sốt.', 'Viêm tuyến vú thường liên quan nhiễm khuẩn; ảnh không xác định được tác nhân.', 'Giữ vệ sinh vắt sữa, tách sữa bất thường; thú y kiểm tra sữa và chọn điều trị, thời gian ngừng sử dụng sữa theo thuốc.'),
 'Coccidiosis': ('Gà ủ rũ, giảm ăn, tiêu chảy; có thể có phân lẫn máu nhưng không phải ca nào cũng vậy.', 'Đơn bào Eimeria; màu phân đơn thuần không đủ xác định bệnh.', 'Giữ chất độn chuồng khô, nước uống sạch; thú y xét nghiệm phân và hướng dẫn thuốc cầu trùng phù hợp.'),
 'New Castle Disease': ('Có thể có triệu chứng hô hấp, tiêu chảy, giảm đẻ hoặc thần kinh như vẹo cổ.', 'Virus Newcastle; ảnh phân không thể xác nhận nhiễm virus.', 'Cách ly đàn nghi bệnh, hạn chế di chuyển và báo thú y. Không tự dùng kháng sinh để chữa virus; kiểm soát dịch và vaccine theo hướng dẫn.'),
 'Salmonella': ('Có thể tiêu chảy, ủ rũ, chậm lớn; biểu hiện phụ thuộc tuổi và tác nhân.', 'Vi khuẩn Salmonella; nhãn ảnh không xác định serovar, cần xét nghiệm.', 'Vệ sinh chuồng, nước và thức ăn; rửa tay sau tiếp xúc. Thú y xét nghiệm và quyết định điều trị, tránh tự dùng kháng sinh.'),
 'Erysipelas': ('Sốt, bỏ ăn, các mảng da đỏ tím có thể dạng hình thoi; thể mạn có thể viêm khớp.', 'Vi khuẩn Erysipelothrix rhusiopathiae; tổn thương ngoài da có thể giống bệnh khác.', 'Cách ly lợn nghi bệnh, đeo găng khi tiếp xúc vùng tổn thương; gọi thú y sớm để xác nhận và kê điều trị thích hợp.'),
 'Greasy_Pig_Disease': ('Da rỉ dịch, nhờn, đóng vảy nâu, thường gặp ở lợn con; ca nặng có thể mất nước.', 'Viêm da tiết dịch thường liên quan Staphylococcus hyicus và vết xước da.', 'Giữ chuồng khô, giảm xây xát và theo dõi bú/ăn. Lợn con yếu hoặc mất nước cần thú y ngay; điều trị phụ thuộc thăm khám và tác nhân.'),
 'Sarcoptic_Mange': ('Ngứa, cọ xát, da dày và đóng vảy, thường thấy ở tai và lan ra thân.', 'Mạt Sarcoptes scabiei var. suis; cần phân biệt với viêm da khác.', 'Thú y xác nhận bằng thăm khám/cạo da, hướng dẫn thuốc diệt mạt cho con bệnh và nhóm tiếp xúc; vệ sinh chuồng và dụng cụ.')
}

def _base_information(label):
    if label=='unknown':
        return {'signs':'Chưa nhận diện được một bệnh thuộc các lớp đang hỗ trợ. Đây không phải kết luận ảnh không có bệnh.','causes':'Có thể là bệnh chưa được hỗ trợ, ảnh không phù hợp, loài khác hoặc mô hình nhận diện sai. Nhóm ngoài phạm vi của lợn đã bổ sung một số bệnh da khác, nhưng chưa bao phủ mọi bệnh.','care':'Kiểm tra đúng loài đã chọn và ảnh rõ vùng cần xem; riêng gà dùng ảnh phân. Nếu con vật có dấu hiệu bất thường, liên hệ thú y dù hệ thống trả unknown. Không chọn thuốc chỉ từ kết quả này.'}
    if label=='oral_signs_unverified':
        return {'signs':'Ảnh có đặc điểm gần nhóm miệng/nước dãi bất thường trong bộ thử nghiệm. Nhóm này chỉ có 6 ảnh nguồn, chưa xác minh căn nguyên.','causes':'Chảy dãi hoặc sùi bọt có thể liên quan bệnh ở miệng, ngộ độc, co giật hoặc bệnh dại; ảnh không phân biệt được các nguyên nhân này.','care':'Tránh chạm vào miệng và nước bọt, không đến gần để chụp thêm. Liên hệ thú y để đánh giá, đặc biệt khi có thay đổi hành vi, khó nuốt hoặc liệt. Nếu người bị cắn/cào hoặc nước bọt vào niêm mạc/vết thương: rửa ngay và đến cơ sở y tế để đánh giá dự phòng dại, không chờ AI. Có thể mở mục sàng lọc nguy cơ dại để xem hướng dẫn tiếp theo.'}
    if label.lower()=='healthy':
        return {'signs':'Ảnh gần với nhóm đối chứng trong dữ liệu huấn luyện.', 'causes':'Kết quả này không loại trừ bệnh và không xác nhận con vật khỏe mạnh.', 'care':GENERAL}
    signs,causes,care=DATA[label]
    return dict(signs=signs,causes=causes,care=care)

def information(label):
    return {**_base_information(label), **guidance(label), 'medications':medication(label)}

def reply(question, last):
    q=question.lower()
    if last and last.get('kind')=='rabies_screening':
        return last['name']+'\n\n'+last['info']['care']+'\n\n'+last['method']
    if any(w in q for w in ['khó thở','co giật','chết','không đứng','bỏ ăn','liệt']):
        return 'Nếu con vật khó thở, co giật, không đứng được, yếu nhanh hoặc có nhiều con chết, hãy liên hệ thú y ngay; đừng chờ kết quả ảnh. Tách con nghi bệnh khi có thể làm an toàn và hạn chế vận chuyển.'
    if any(w in q for w in ['dại','cắn người']):
        return 'Web chưa hỗ trợ nhận diện bệnh dại. Ảnh sùi bọt mép không đủ kết luận. Tránh tiếp xúc nước bọt và liên hệ thú y; nếu người bị cắn/cào hoặc nước bọt vào vết thương, rửa bằng xà phòng và nước chảy khoảng 15 phút, đến cơ sở y tế ngay để đánh giá dự phòng dại.'
    if not last:
        return 'Bạn chọn loài rồi gửi ảnh vùng tổn thương; riêng gà dùng ảnh phân. Sau khi có kết quả, bạn có thể hỏi về dấu hiệu, nguyên nhân hoặc hướng xử trí. Phần chat trả lời từ nội dung tham khảo có sẵn, chưa hỗ trợ tư vấn tự do.'
    info=last['info']; name=last['name']
    if last.get('label'):
        info=information(last['label'])
    if any(w in q for w in ['nguyên nhân','vì sao','tại sao']): text=info['causes']
    elif any(w in q for w in ['dấu hiệu','triệu chứng','biểu hiện']): text=info['signs']
    elif any(w in q for w in ['phòng','ngừa','vệ sinh','vaccine','vắc xin']): text=info.get('prevention',GENERAL)
    elif any(w in q for w in ['khẩn','khi nào','đi khám','nguy hiểm']): text=info.get('urgent',GENERAL)
    elif any(w in q for w in ['theo dõi','xét nghiệm','kiểm tra']): text=info.get('monitoring',GENERAL)
    elif any(w in q for w in ['thuốc','liều']): text=info.get('medications',info.get('treatment',info['care']))
    elif any(w in q for w in ['chữa','điều trị']): text=info.get('treatment',info['care'])+'\n\nThuốc tham khảo:\n'+info.get('medications','Trao đổi với thú y sau khi xác nhận nguyên nhân.')
    elif any(w in q for w in ['xử trí','làm gì','chăm sóc']): text=info['care']
    elif any(w in q for w in ['tư vấn','chi tiết','tổng hợp']): text='\n\n'.join(title+':\n'+info.get(key,GENERAL) for key,title in [('care','Xử trí ban đầu'),('treatment','Hướng điều trị'),('prevention','Phòng tránh'),('urgent','Khi cần thú y ngay'),('monitoring','Theo dõi')])
    else: return f'Kết quả gần nhất là nhãn “{name}”, chưa phải chẩn đoán. Mình có thể giải thích dấu hiệu, nguyên nhân hoặc hướng xử trí của nhãn này. Hãy chọn một câu hỏi gợi ý bên dưới.'
    return f'Tham khảo cho nhãn “{name}” (chưa xác nhận bệnh):\n\n{text}'

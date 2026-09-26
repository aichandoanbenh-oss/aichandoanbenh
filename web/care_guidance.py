"""General educational care pathways; not individualized drug prescriptions."""

# treatment, prevention, urgent referral, monitoring / confirmation
GUIDANCE = {
    'Dermatitis': (
        'Khám da, kiểm tra ký sinh trùng và tế bào học để tìm nguyên nhân. Thú y có thể chọn thuốc diệt ký sinh trùng, kháng nấm hoặc điều trị nhiễm khuẩn khi có chỉ định; kiểm soát ngứa đi kèm điều trị nguyên nhân. Không tự bôi kem người hoặc corticoid vì có thể làm nặng nhiễm trùng.',
        'Kiểm soát bọ chét theo lịch phù hợp, giữ chỗ nằm sạch và khô, dùng sản phẩm tắm dành cho chó. Rửa và làm khô đồ dùng; tránh đổi nhiều sản phẩm cùng lúc để dễ phát hiện yếu tố kích ứng.',
        'Khám trong ngày nếu da đau, có mủ, mùi hôi, tổn thương lan nhanh hoặc chó bỏ ăn. Khó thở, sưng mặt hoặc suy sụp cần cấp cứu.',
        'Ghi mức ngứa, vị trí và diện tích tổn thương, mức ăn uống mỗi ngày. Cung cấp lịch tẩy ký sinh trùng, thuốc đã dùng và sản phẩm mới cho thú y.'),
    'Fungal_infections': (
        'Thú y cần phân biệt nấm với mạt, vi khuẩn và dị ứng bằng xét nghiệm phù hợp. Tùy vị trí, mức lan rộng và tác nhân, có thể dùng điều trị tại chỗ hoặc thuốc kháng nấm toàn thân; tái khám để đánh giá đáp ứng trước khi ngừng thuốc.',
        'Hạn chế dùng chung lược, khăn và chỗ nằm; hút sạch lông, giặt đồ dùng và vệ sinh bề mặt. Đeo găng khi chăm sóc vùng bệnh, rửa tay; hạn chế trẻ nhỏ và người suy giảm miễn dịch tiếp xúc tổn thương.',
        'Khám sớm nếu tổn thương lan rộng, có mủ hoặc chó mệt, bỏ ăn. Người tiếp xúc xuất hiện tổn thương da nên đi khám và báo tiền sử tiếp xúc vật nuôi.',
        'Theo dõi tổn thương mới, mức ngứa và tình trạng lông mọc lại. Hình dạng tròn hoặc đèn soi đơn lẻ không đủ xác nhận nấm; có thể cần soi mẫu, nuôi cấy hoặc xét nghiệm khác.'),
    'Hypersensitivity': (
        'Loại trừ bọ chét, mạt và nhiễm trùng trước. Thú y có thể chỉ định kiểm soát ngứa, xử lý viêm tai và thử chế độ ăn loại trừ có giám sát nếu nghi dị ứng thức ăn. Không tự đổi thức ăn liên tục hoặc dùng thuốc chống dị ứng của người.',
        'Kiểm soát bọ chét cho các vật nuôi cùng nhà theo hướng dẫn. Giặt chỗ nằm, tránh sản phẩm gây kích ứng đã nhận biết. Nếu đang thử khẩu phần loại trừ, không cho thêm đồ ăn vặt ngoài kế hoạch.',
        'Sưng mặt, khó thở hoặc ngất cần cấp cứu. Khám sớm khi gãi chảy máu, tai đau/hôi hoặc ngứa khiến mất ngủ, bỏ ăn.',
        'Lập nhật ký thức ăn, thời điểm ngứa, mùa, nơi đi chơi và sản phẩm vệ sinh. Theo dõi da, tai và bàn chân; dị ứng thường cần kiểm soát lâu dài, không chỉ chữa đợt ngứa.'),
    'demodicosis': (
        'Xác nhận bằng cạo da hoặc xét nghiệm thích hợp. Thú y lựa chọn thuốc diệt mạt được phép dùng cho chó và xử lý nhiễm khuẩn thứ phát nếu có. Ca toàn thân hoặc khởi phát ở chó trưởng thành cần tìm bệnh nền; không tự dùng ivermectin hay thuốc diệt côn trùng.',
        'Duy trì dinh dưỡng, chăm sóc da và kiểm soát bệnh nền. Không dùng thuốc ức chế miễn dịch khi chưa có chỉ định. Trao đổi với thú y về phối giống nếu chó mắc thể toàn thân có khả năng liên quan di truyền.',
        'Khám sớm nếu rụng lông lan rộng, bàn chân sưng, da có mủ hoặc đau. Sốt, yếu hay bỏ ăn cần đánh giá trong ngày.',
        'Chụp vùng da theo thời gian và tái kiểm tra mẫu da theo hẹn. Lông mọc lại không tự chứng minh đã kiểm soát mạt; không tự ngừng điều trị sớm.'),
    'foot_and_mouth': (
        'Báo thú y địa phương ngay để khám, lấy mẫu và tổ chức kiểm soát dịch. Không có thuốc tự dùng từ ảnh để loại bỏ virus. Chăm sóc hỗ trợ gồm nước sạch, thức ăn mềm dễ ăn và xử lý tổn thương theo thú y; thuốc giảm đau hoặc điều trị bội nhiễm chỉ dùng khi được chỉ định.',
        'Tiêm phòng theo chương trình địa phương; kiểm soát con giống và cách ly đàn mới nhập theo thú y. Tách dụng cụ, hạn chế người/xe vào khu bệnh, làm sạch chất hữu cơ trước khi khử trùng. Không bán chạy hay vận chuyển con nghi bệnh.',
        'Nghi lở mồm long móng cần báo ngay, đặc biệt khi nhiều con chảy dãi, loét miệng và khập khiễng. Con non yếu đột ngột, khó thở hoặc không uống được cần trợ giúp khẩn.',
        'Ghi số con có triệu chứng, ngày khởi phát, lịch vaccine, nhập đàn và vận chuyển gần đây. Theo dõi uống nước, khả năng đứng/đi; không tự chọc vỡ mụn nước để kiểm tra.'),
    'lumpy_skin': (
        'Liên hệ thú y để xác nhận và quản lý ổ dịch. Điều trị chủ yếu hỗ trợ ăn uống, giảm đau và chăm sóc tổn thương; kháng sinh chỉ dùng khi thú y đánh giá có nhiễm khuẩn thứ phát. Không tự chích, nặn hay cắt các nốt da.',
        'Tiêm vaccine theo hướng dẫn thú y địa phương, kiểm soát côn trùng hút máu và nước đọng. Không dùng chung kim tiêm, làm sạch dụng cụ, kiểm soát nhập đàn và hạn chế di chuyển con nghi bệnh.',
        'Báo thú y khi xuất hiện nhiều nốt da kèm sốt hoặc lan trong đàn. Khó thở, sưng nhiều, không đứng được hoặc không uống cần xử trí khẩn.',
        'Ghi thời điểm xuất hiện nốt, số con bệnh, lượng ăn/uống và sữa. Theo dõi vết loét, ruồi bâu, dịch tiết; xác nhận bằng thăm khám và xét nghiệm theo thú y.'),
    'mastitis': (
        'Thú y kiểm tra bầu vú, sữa và có thể lấy mẫu trước điều trị nếu không làm chậm cấp cứu. Điều trị tùy mức nặng và tác nhân, có thể gồm dịch, giảm đau và kháng sinh phù hợp. Không tự bơm thuốc vào núm vú; tuân thủ thời gian ngừng khai thác sữa/thịt của thuốc.',
        'Giữ nền nằm khô, tay và thiết bị vắt sạch; dùng quy trình vệ sinh núm vú trước/sau vắt phù hợp. Vắt con bệnh sau cùng hoặc bằng dụng cụ riêng. Tách sữa bất thường và sữa đang trong thời gian ngừng thuốc khỏi thực phẩm.',
        'Sốt, bỏ ăn, yếu, mất nước, bầu vú đổi màu hoặc sữa loãng bất thường kèm suy sụp là tình huống khẩn. Đừng chỉ chờ ảnh đánh giá bầu vú.',
        'Ghi khoang vú bị ảnh hưởng, màu/cặn sữa, lượng sữa và thuốc đã dùng. Viêm vú dưới lâm sàng có thể không thấy trong ảnh; cần thử sữa hoặc kiểm tra tế bào theo chương trình đàn.'),
    'Coccidiosis': (
        'Thú y đánh giá đàn, xét nghiệm phân và khi cần khám bệnh tích để chọn thuốc cầu trùng. Chăm sóc nước uống và tình trạng mất nước; không trộn nhiều thuốc hoặc tăng liều khi chưa rõ nguyên nhân. Với gà thực phẩm, tuân thủ nhãn thuốc và thời gian ngừng thuốc.',
        'Giữ chất độn khô, sửa máng uống rò rỉ, giảm quá tải và tách nhóm tuổi. Dọn phân và vệ sinh dụng cụ; noãn nang có thể chịu được nhiều chất sát trùng thông thường. Chương trình vaccine hoặc thuốc phòng cần do thú y thiết kế phù hợp đàn.',
        'Phân máu, gà yếu nhanh, bỏ uống hoặc số chết tăng cần thú y trong ngày. Không mặc định mọi phân đỏ đều do cầu trùng.',
        'Ghi tuổi đàn, số con bệnh/chết, lượng ăn/uống và chương trình phòng cầu trùng. Lấy mẫu phân theo hướng dẫn, đánh giá cả đàn thay vì chỉ màu của một bãi phân.'),
    'New Castle Disease': (
        'Báo thú y để xét nghiệm, phân biệt với cúm gia cầm và nguyên nhân khác. Không có kháng sinh chữa virus Newcastle; xử trí ổ dịch và chăm sóc hỗ trợ phải theo thú y. Không tự bán, giết mổ hoặc di chuyển đàn nghi nhiễm.',
        'Thực hiện chương trình vaccine đúng tuổi và bảo quản đúng hướng dẫn. Kiểm soát người, dụng cụ và con giống; ngăn tiếp xúc chim hoang, vệ sinh giữa các lứa. Vaccine không thay thế an toàn sinh học.',
        'Gà chết hàng loạt, khó thở, vẹo cổ, liệt hoặc giảm đẻ đột ngột cần báo thú y ngay. Tránh tự mổ khám con chết.',
        'Ghi diễn biến chết, triệu chứng hô hấp/thần kinh và lịch vaccine. Ảnh phân không phân biệt Newcastle với nhiều bệnh truyền nhiễm khác; cần lấy mẫu đúng quy trình.'),
    'Salmonella': (
        'Cần xác nhận bằng xét nghiệm và đánh giá mục đích đàn, tuổi cùng tác nhân. Kháng sinh nếu dùng phải theo thú y và xét nghiệm phù hợp; điều trị triệu chứng không bảo đảm loại bỏ tình trạng mang trùng. Chăm sóc nước, nhiệt độ chuồng và kiểm soát nguồn lây đi kèm.',
        'Chọn con giống được kiểm soát, bảo vệ thức ăn/nước khỏi phân và chuột. Rửa tay sau tiếp xúc gia cầm, tách giày/dụng cụ chăn nuôi khỏi bếp. Không ăn trứng/thịt sống hoặc chưa chín; không sử dụng sản phẩm từ đàn bệnh trái hướng dẫn thú y.',
        'Gà con tiêu chảy nhiều, mất nước, yếu hoặc số chết tăng cần khám sớm. Người chăm sóc sốt, tiêu chảy sau tiếp xúc cần tư vấn y tế.',
        'Ghi nguồn giống, tuổi đàn, số bệnh/chết và thuốc đã sử dụng. Theo dõi phân và ăn uống nhưng không dùng phân trở lại bình thường làm bằng chứng sạch mầm bệnh.'),
    'Erysipelas': (
        'Thú y cần khám sớm, phân biệt với các bệnh gây sốt/xuất huyết khác và chỉ định kháng sinh thích hợp khi xác nhận hoặc có chỉ định lâm sàng. Hỗ trợ nước, nghỉ ngơi và giảm đau theo thú y; tổn thương khớp hoặc tim mạn cần đánh giá riêng. Tuân thủ thời gian ngừng thuốc trước xuất bán.',
        'Tiêm phòng theo chương trình đàn, kiểm soát nhập đàn và vệ sinh chuồng/dụng cụ. Đeo găng, che vết thương khi chăm sóc vì tác nhân có thể lây sang người qua da tổn thương. Không chuyển con bệnh sang đàn khác.',
        'Sốt, bỏ ăn, da tím, khó thở, đi lại đau hoặc chết đột ngột cần thú y ngay. Không khẳng định bệnh đóng dấu chỉ vì thấy mảng da hình thoi.',
        'Ghi diễn biến tổn thương, số con bệnh, lịch vaccine và thuốc đã dùng. Theo dõi uống nước, đi lại và ăn uống; lấy mẫu trước kháng sinh nếu thú y thấy phù hợp và không trì hoãn điều trị.'),
    'Greasy_Pig_Disease': (
        'Thú y đánh giá mất nước và nhiễm trùng, cân nhắc lấy mẫu/kháng sinh đồ để chọn kháng sinh khi cần. Chăm sóc dịch và vệ sinh da bằng sản phẩm phù hợp cho lợn con phải theo hướng dẫn. Không bóc vảy mạnh, bôi chất ăn mòn hoặc tự phối nhiều thuốc.',
        'Giữ ô đẻ sạch, khô; vệ sinh nái và dụng cụ, giảm cạnh sắc và cắn nhau gây trầy da. Theo dõi bú sữa đầu và dinh dưỡng lợn con. Tách nhóm bệnh bằng dụng cụ riêng, vệ sinh giữa các lứa.',
        'Lợn con bỏ bú, yếu, da nhăn, tổn thương lan nhanh hoặc nhiều con cùng bị cần thú y ngay vì có thể mất nước nhanh.',
        'Kiểm tra bú/ăn, độ hoạt bát và vùng rỉ dịch nhiều lần trong ngày ở lợn con. Ghi tuổi, số con cùng ổ bị bệnh, thuốc và chất sát trùng đã dùng; đánh giá lại sớm nếu xấu đi.'),
    'Sarcoptic_Mange': (
        'Thú y xác nhận và lập kế hoạch thuốc diệt mạt cho con bệnh cùng nhóm tiếp xúc khi cần. Thuốc, đường dùng và lịch nhắc phụ thuộc sản phẩm, tuổi và tình trạng đàn; không tự suy liều từ loài khác. Điều trị nhiễm khuẩn thứ phát nếu có chỉ định, tuân thủ thời gian ngừng thuốc.',
        'Kiểm tra và cách ly lợn mới nhập theo quy trình đàn, tránh dùng chung dụng cụ bẩn. Làm sạch ô chuồng và đồ dùng, phối hợp xử lý các nhóm tiếp xúc để giảm tái nhiễm.',
        'Khám sớm khi ngứa dữ dội, trầy loét, có mủ, giảm ăn hoặc chậm lớn rõ. Da đỏ tím kèm sốt cao cần đánh giá nguyên nhân khác, không mặc định là ghẻ.',
        'Theo dõi cọ xát, tổn thương tai và da, khả năng ăn/tăng trưởng. Tái khám theo lịch; ngứa giảm chưa đủ chứng minh đã kiểm soát hết mạt.')
}
GUIDANCE['ringworm'] = GUIDANCE['Fungal_infections']

SPECIAL = {
    'unknown': (
        'Chưa có nhãn bệnh phù hợp nên không gợi ý thuốc. Kiểm tra loài và loại ảnh; nếu có triệu chứng, để thú y khám trực tiếp thay vì thử điều trị theo điểm mô hình.',
        'Duy trì vệ sinh, thức ăn/nước sạch và lịch phòng bệnh phù hợp loài. Không dùng kết quả unknown để quyết định bỏ tiêm phòng hoặc nhập đàn.',
        'Khó thở, co giật, không đứng được, chảy máu nhiều hoặc nhiều con cùng bệnh cần thú y ngay bất kể kết quả ảnh.',
        'Ghi triệu chứng thực tế, thời gian khởi phát và con tiếp xúc. Chụp rõ vùng tổn thương nếu an toàn; riêng gà mô hình dùng ảnh phân.'),
    'healthy': (
        'Không dùng thuốc chỉ vì đã gửi ảnh. Nếu con vật có triệu chứng, cần khám dù nhãn ảnh là khỏe mạnh; ảnh không đánh giá được bệnh bên trong hoặc giai đoạn sớm.',
        'Duy trì khẩu phần phù hợp, nước sạch, vệ sinh và tiêm phòng/kiểm soát ký sinh trùng theo loài và thú y địa phương. Kiểm soát con mới nhập đàn.',
        'Bỏ ăn kéo dài, khó thở, yếu nhanh, co giật hoặc đàn chết bất thường cần khám, không chờ kết quả ảnh thay đổi.',
        'Theo dõi ăn uống, vận động, phân, tăng trưởng hoặc sản lượng. Ghi thay đổi so với bình thường và khám định kỳ theo nhu cầu đàn.'),
    'oral_signs_unverified': (
        'Không suy ra bệnh dại hoặc chọn thuốc từ ảnh nước dãi. Bệnh miệng, ngộ độc và rối loạn thần kinh cần xử trí khác nhau; liên hệ thú y ngay để hướng dẫn tiếp cận an toàn. Không móc miệng, ép uống, tự gây nôn hoặc cho thuốc khi chó khó nuốt/co giật.',
        'Tiêm phòng dại định kỳ theo thú y và quản lý chó tránh thả rông. Cất thuốc, hóa chất và mồi độc ngoài tầm với. Tránh tiếp xúc chó lạ có hành vi bất thường; không đến gần chó nghi dại để chụp thêm ảnh.',
        'Khó nuốt, liệt, co giật, thay đổi hành vi hoặc nghi ngộ độc cần thú y khẩn. Người bị cắn/cào hoặc nước bọt vào vết thương/niêm mạc: rửa vết thương với xà phòng và nước chảy khoảng 15 phút, rửa niêm mạc bằng nước sạch rồi đến cơ sở y tế ngay để đánh giá dự phòng dại.',
        'Chỉ ghi nhận từ khoảng cách an toàn: thời điểm khởi phát, vaccine dại, tiếp xúc chó lạ/chất độc. Không tự bắt giữ hoặc kiểm tra miệng; nhờ thú y/cơ quan có trách nhiệm hướng dẫn. Mô hình này không loại trừ dại.')
}

def guidance(label):
    key = 'healthy' if label.lower() == 'healthy' else label
    values = GUIDANCE.get(key) or SPECIAL[key]
    return dict(zip(('treatment', 'prevention', 'urgent', 'monitoring'), values))

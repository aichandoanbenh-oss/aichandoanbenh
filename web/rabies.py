"""Conservative referral rules; not a validated diagnostic score."""
from typing import Literal
from pydantic import BaseModel, ConfigDict

Answer=Literal['yes','no','unknown']
QUESTIONS={
 'human_exposure':'Có người bị cắn/cào hoặc nước bọt tiếp xúc mắt, miệng hay vết thương không?',
 'animal_exposure':'Chó đã tiếp xúc hoặc bị động vật nghi dại cắn không?',
 'behavior':'Chó có thay đổi hành vi bất thường, hung dữ hoặc kích động không?',
 'neurologic':'Chó có đi loạng choạng, liệt hoặc co giật không?',
 'swallowing':'Chó có khó nuốt hoặc chảy nhiều nước bọt bất thường không?',
 'vaccinated':'Có xác nhận chó được tiêm phòng dại còn hiệu lực không?'
}
class Screening(BaseModel):
    model_config=ConfigDict(extra='forbid')
    human_exposure:Answer
    animal_exposure:Answer
    behavior:Answer
    neurologic:Answer
    swallowing:Answer
    vaccinated:Answer

def assess(data:Screening):
    answers=data.model_dump()
    signs=[QUESTIONS[k] for k in ['behavior','neurologic','swallowing'] if answers[k]=='yes']
    urgent=bool(signs) or data.animal_exposure=='yes'
    human=data.human_exposure=='yes'
    title=('Có phơi nhiễm ở người — cần đến cơ sở y tế ngay' if human else
           'Có dấu hiệu hoặc tiền sử cần đánh giá nghi ngờ dại' if urgent else
           'Chưa đủ cơ sở xác định nghi ngờ dại — không loại trừ bệnh')
    reasons=[]
    if human:reasons.append('Bạn khai báo có người tiếp xúc có nguy cơ; cần đánh giá dự phòng sau phơi nhiễm, không chờ chó biểu hiện bệnh.')
    if data.animal_exposure=='yes':reasons.append('Có tiền sử tiếp xúc động vật nghi dại theo khai báo.')
    if signs:reasons.append('Có dấu hiệu bất thường theo khai báo. Những dấu hiệu này cũng có thể do bệnh khác, không đặc hiệu cho dại.')
    if not reasons:reasons.append('Chưa ghi nhận dấu hiệu hoặc tiền sử rõ ràng từ câu trả lời. Điều này không chứng minh chó không mắc dại.')
    if 'unknown' in answers.values():reasons.append('Một số thông tin chưa rõ; không coi thông tin thiếu là câu trả lời “không”.')
    if data.vaccinated!='yes':reasons.append('Chưa xác nhận tiêm phòng còn hiệu lực; hỏi thú y về lịch tiêm, không dùng tình trạng tiêm đơn lẻ để xác định bệnh.')
    care=['Tránh chạm vào miệng, nước bọt; không tự bắt, khống chế, khám miệng hoặc đến gần để chụp ảnh. Giữ trẻ em và vật nuôi khác tránh xa.',
          'Nếu có thể làm an toàn, giữ khoảng cách và ngăn người khác tiếp cận. Liên hệ thú y/cơ quan địa phương để được hướng dẫn quản lý và theo dõi con vật.']
    if human or data.human_exposure=='unknown':care.insert(0,'Nếu bị cắn/cào hoặc nước bọt vào mắt, miệng hay vết thương: rửa vết thương bằng xà phòng và nước chảy khoảng 15 phút; rửa niêm mạc bằng nhiều nước sạch. Đến cơ sở y tế ngay để đánh giá vaccine và huyết thanh/kháng thể dự phòng; không chờ kết quả AI hoặc theo dõi con vật mới đi khám.')
    if urgent:care.append('Liên hệ thú y ngay về các dấu hiệu/tiền sử đã khai báo. Không có thuốc tự chữa bệnh dại tại nhà.')
    else:care.append('Theo dõi từ khoảng cách an toàn và trao đổi với thú y về tiêm phòng. Nếu xuất hiện hành vi bất thường, khó nuốt hoặc liệt, liên hệ thú y ngay.')
    return {'kind':'rabies_screening','species':'dog','name':title,'answers':answers,'reasons':reasons,'human_referral':human,'veterinary_referral':urgent,
            'info':{'signs':' '.join(reasons),'causes':'Bệnh dại do virus, thường lây qua nước bọt động vật nhiễm bệnh. Ảnh, triệu chứng và lịch tiêm không đủ xác nhận hay loại trừ bệnh.','care':'\n\n'.join(care)},
            'method':'Sàng lọc theo câu trả lời; quy tắc hướng dẫn liên hệ chuyên môn, chưa được kiểm định lâm sàng. Không phân tích ảnh để đánh giá dại, không tính xác suất mắc bệnh.',
            'sources':[{'name':'WHO — Rabies','url':'https://www.who.int/news-room/fact-sheets/detail/rabies'},{'name':'WOAH — Rabies','url':'https://www.woah.org/en/disease/rabies/'}]}

from pydantic import BaseModel, Field
from typing import Optional, List


class AuditCriterion(BaseModel):
    question_or_task: str = Field(
        description="Câu hỏi gợi ý audit tập trung vào tư duy xử lý sự cố & vận hành thực tế bám sát tài liệu"
    )
    expected_answer_keywords: str = Field(
        description="Từ khóa hoặc ý chính bắt buộc intern phải trả lời/làm được"
    )


class MultipleChoiceQuestion(BaseModel):
    question: str = Field(description="Câu hỏi trắc nghiệm kiểm tra kiến thức của subtopic")
    options: List[str] = Field(description="Danh sách 4 phương án trắc nghiệm [A. ..., B. ..., C. ..., D. ...]")
    correct_answer: str = Field(description="Đáp án đúng (VD: 'A' hoặc 'A. ...')")
    explanation: str = Field(description="Giải thích ngắn gọn lý do đúng bám sát tài liệu PDF")


class SubTopic(BaseModel):
    title: str = Field(description="Tên chuyên đề con bám sát tài liệu")
    summary: str = Field(description="Tóm tắt ngắn 1-2 câu về nội dung phần này")
    lecture_content: str = Field(
        default="",
        description="Bài giảng Lý thuyết & Cơ chế Vận hành Chuyên sâu (Markdown 200-400 từ) giải thích chi tiết bản chất kỹ thuật, kiến trúc, luồng xử lý và nguyên lý từ tài liệu như 1 Leader đang đào tạo Intern"
    )
    production_gotchas: str = Field(
        default="",
        description="Kinh nghiệm thực chiến, bẫy thường gặp & lưu ý sản xuất (Senior Gotchas) khi triển khai thực tế bám sát bài học"
    )
    lab_exercise: str = Field(
        default="",
        description="Kịch bản thực hành Lab & Các bước/Lệnh CLI/Cấu hình chi tiết cho Intern tự thực hành"
    )
    practical_guide: str = Field(default="", description="Hướng dẫn học & lưu ý thực hành tóm tắt")
    audit_checklist: List[AuditCriterion] = Field(default=[], description="Bộ câu hỏi gợi ý dành cho TechLead khi Audit")
    quiz_questions: List[MultipleChoiceQuestion] = Field(default=[], description="Bộ câu hỏi trắc nghiệm kiểm tra kiến thức cho Intern")


class ConceptExplanation(BaseModel):
    term: str = Field(description="Thuật ngữ / Khái niệm chìa khóa")
    definition: str = Field(description="Giải thích bản chất khái niệm 1-2 câu dễ hiểu")


class DevOpsModule(BaseModel):
    module_name: str = Field(description="Tên Module lớn chuẩn hóa bám sát tài liệu")
    summary: str = Field(default="", description="Tóm tắt nội dung chính của Module")
    estimated_study_days: int = Field(default=3, description="Thời gian ước tính intern cần đọc và làm lab (ngày)")
    cloud_application: str = Field(default="", description="Ứng dụng thực tế trên Cloud (AWS/GCP/Docker/K8s) và mô hình hạ tầng phù hợp (Microservices, CI/CD...)")
    key_concepts: List[str] = Field(default=[], description="Danh sách thuật ngữ/khái niệm cốt lõi")
    concept_explanations: List[ConceptExplanation] = Field(default=[], description="Giải thích chi tiết từng từ khóa cốt lõi")
    sub_topics: List[SubTopic] = Field(default=[], description="Danh sách các chuyên đề con")


class DevOpsCurriculum(BaseModel):
    document_title: str = Field(default="DevOps Training Roadmap", description="Tên tổng quan tài liệu")
    modules: List[DevOpsModule] = Field(default=[], description="Danh sách các Modules học tập")

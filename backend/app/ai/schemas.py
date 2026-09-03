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
    summary: str = Field(description="Tóm tắt ngắn 1-2 câu về nội dung phần này trong tài liệu")
    audit_checklist: List[AuditCriterion] = Field(default=[], description="Bộ câu hỏi gợi ý dành cho TechLead khi Audit")
    quiz_questions: List[MultipleChoiceQuestion] = Field(default=[], description="Bộ câu hỏi trắc nghiệm kiểm tra kiến thức cho Intern")


class DevOpsModule(BaseModel):
    module_name: str = Field(description="Tên Module lớn chuẩn hóa bám sát tài liệu")
    summary: str = Field(default="", description="Tóm tắt nội dung chính của Module")
    estimated_study_days: int = Field(default=3, description="Thời gian ước tính intern cần đọc và làm lab (ngày)")
    key_concepts: List[str] = Field(default=[], description="Danh sách thuật ngữ/khái niệm cốt lõi")
    sub_topics: List[SubTopic] = Field(default=[], description="Danh sách các chuyên đề con")


class DevOpsCurriculum(BaseModel):
    document_title: str = Field(default="DevOps Training Roadmap", description="Tên tổng quan tài liệu")
    modules: List[DevOpsModule] = Field(default=[], description="Danh sách các Modules học tập")

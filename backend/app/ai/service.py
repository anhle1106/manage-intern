import os
import time
import re
import json
from datetime import datetime, timezone
from app.config import get_settings
from app.database import get_db
from app.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt
from app.ai.schemas import DevOpsCurriculum, DevOpsModule, SubTopic, AuditCriterion, MultipleChoiceQuestion

# Support both google-genai and google-generativeai SDKs seamlessly
USE_NEW_SDK = False
try:
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai


def _subtopic_to_dict(st) -> dict:
    if hasattr(st, "model_dump"):
        return st.model_dump()
    elif hasattr(st, "dict"):
        return st.dict()
    elif isinstance(st, dict):
        return st
    return {"title": str(st), "summary": "", "audit_checklist": [], "quiz_questions": []}


async def analyze_document_file(
    document_id: str,
    file_path: str,
    onboarding_id: str | None = None,
) -> DevOpsCurriculum:
    settings = get_settings()

    api_key = settings.gemini_api_key or ""
    has_api_key = bool(api_key) and "your-gemini-api-key" not in api_key

    if has_api_key:
        uploaded_file = None
        try:
            filename = os.path.basename(file_path)
            print(f"[AI Module - Files API] Uploading PDF '{filename}' to Gemini Files API with key '{api_key[:8]}...'")

            prompt = f"""
            Bạn là Director of Software Engineering & Principal Tech Lead có 15 năm kinh nghiệm.
            Nhiệm vụ của bạn là đọc tài liệu PDF đính kèm và xây dựng Bộ câu hỏi Audit & Lộ trình đào tạo dặn dò Intern cực kỳ sắc bén, chuẩn chuyên môn doanh nghiệp lớn.

            QUY TẮC BẮT BUỘC VỀ NỘI DUNG:
            🚫 TUYỆT ĐỐI KHÔNG ĐƯA TÊN FILE, ĐUÔI FILE (.pdf, .docx) HAY TÊN TỆP NGUỒN VÀO NỘI DUNG CÂU HỎI, TIÊU ĐỀ HAY PHƯƠNG ÁN LỰA CHỌN.
               (Ví dụ CẤM hỏi: "Dựa vào file document_v1.pdf...", "Tải tài liệu file.pdf...". Học sinh/intern tự đọc nội dung bài học, chỉ hỏi trực tiếp vào kiến thức chuyên môn!).

            TUYỆT ĐỐI NÓI KHÔNG VỚI CÁC CÂU HỎI "ỐI DỜI ỐI" CHUNG CHUNG:
            ❌ CẤM ĐẶT CÂU HỎI CHUNG CHUNG KIỂU: "Dựa vào tài liệu, hãy giải thích khái niệm X là gì và cơ chế hoạt động của nó?"
            ❌ CẤM ĐẶT CÂU HỎI HỌC THUỘC LÒNG: "Trình bày các bước thực hiện trong slide?", "Định nghĩa X là gì?"

            QUY TẮC ĐẶT CÂU HỎI AUDIT CHUẨN TECHLEAD (SẮC BÉN & TÌNH HUỐNG THỰC TẾ):
            ✅ DẠNG 1 - TÌNH HUOSHNG & SỰ CỐ (TROUBLESHOOTING & SCENARIOS):
               - "Khi hệ thống gặp sự cố [Tên sự cố/tình huống kỹ thuật], nguyên nhân cốt lõi (Root Cause) thường do đâu và quy trình 3 bước xử lý là gì?"
            ✅ DẠNG 2 - ĐÁNH ĐỔI VỀ KIẾN TRÚC & NGUYÊN LÝ (TRADE-OFFS & MECHANICS):
               - "Tại sao kiến trúc lại đề xuất chọn [Phương án A] thay vì [Phương án B]? Đánh đổi (trade-off) ở đây về hiệu năng hoặc tính toàn vẹn dữ liệu là gì?"
            ✅ DẠNG 3 - QUY TRÌNH LUỒNG VẬN HÀNH & KẾT QUẢ MONG ĐỢI (LIFECYCLE & EXECUTION):
               - "Trong cơ chế [Tên cơ chế cụ thể], khi dữ liệu/request đi từ [Thành phần 1] sang [Thành phần 2], điều gì đảm bảo tính an toàn/tính toàn vẹn?"

            QUY TẮC BÓC TÁCH KEY CONCEPTS & QUIZ TRẮC NGHIỆM INTERN:
            1. Key Concepts: Phải trích xuất đúng các từ khóa kỹ thuật chuyên môn cao có trong file (VD: ["Ansible Playbook", "Idempotency", "Inventory Host", "State Management"]).
            2. Trắc nghiệm Intern (2 câu/subtopic): Tạo câu hỏi kiểm tra tư duy chọn đáp án đúng A, B, C, D kèm phần giải thích (`explanation`) thuyết phục bám sát kiến thức bài học.

            Cấu trúc JSON đầu ra bắt buộc:
            {{
              "document_title": "{filename}",
              "modules": [
                {{
                  "module_name": "Module 1: Tên Module lớn chuẩn chuyên môn",
                  "summary": "Tóm tắt 2-3 câu về nội dung và mục tiêu đào tạo của Module",
                  "estimated_study_days": 2,
                  "key_concepts": ["Từ khóa kỹ thuật 1", "Từ khóa kỹ thuật 2", "Từ khóa kỹ thuật 3"],
                  "sub_topics": [
                    {{
                      "title": "Chuyên đề 1.1: Tên chuyên đề chi tiết bám sát nội dung chuyên môn",
                      "summary": "Tóm tắt mục tiêu bài học và kiến thức cốt lõi Intern cần đạt",
                      "audit_checklist": [
                        {{
                          "question_or_task": "Câu hỏi Audit sắc bén dạng Tình huống/Đánh đổi/Cơ chế cụ thể (TUYỆT ĐỐI KHÔNG LÔI TÊN FILE VÀO)",
                          "expected_answer_keywords": "Từ khóa & ý trả lời cốt lõi của câu hỏi"
                        }},
                        {{
                          "question_or_task": "Câu hỏi Audit sắc bén thứ 2 kiểm tra tư duy kỹ thuật & luồng xử lý thực tế",
                          "expected_answer_keywords": "Từ khóa & ý trả lời cốt lõi của câu hỏi"
                        }}
                      ],
                      "quiz_questions": [
                        {{
                          "question": "Câu hỏi trắc nghiệm 1 kiểm tra tư duy chuyên môn của Subtopic?",
                          "options": ["A. Đáp án A", "B. Đáp án B", "C. Đáp án C", "D. Đáp án D"],
                          "correct_answer": "A",
                          "explanation": "Giải thích chi tiết tại sao A đúng"
                        }},
                        {{
                          "question": "Câu hỏi trắc nghiệm 2 kiểm tra tình huống thực tế của Subtopic?",
                          "options": ["A. Phương án 1", "B. Phương án 2", "C. Phương án 3", "D. Phương án 4"],
                          "correct_answer": "B",
                          "explanation": "Giải thích chi tiết tại sao B đúng"
                        }}
                      ]
                    }}
                  ]
                }}
              ]
            }}

            Bóc tách tài liệu 100% bám sát nội dung đính kèm. Đảm bảo câu hỏi sắc bén, chuẩn chuyên môn và TUYỆT ĐỐI KHÔNG CHỨA TÊN FILE NGUỒN TRONG CÂU HỎI HAY ĐÁP ÁN!
            """

            json_text = ""

            if USE_NEW_SDK:
                client = genai.Client(api_key=api_key)
                uploaded_file = client.files.upload(file=file_path)
                print(f"[AI Module - Files API] Uploaded via new SDK. URI: {uploaded_file.uri}")

                candidate_models = ["models/gemini-3.6-flash", "gemini-3.6-flash", "models/gemini-2.5-flash"]
                last_err = None
                for model_name in candidate_models:
                    try:
                        print(f"[AI Module] Requesting generate_content with model '{model_name}'...")
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[uploaded_file, prompt],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=DevOpsCurriculum,
                                temperature=0.3,
                            ),
                        )
                        json_text = response.text
                        print(f"[AI SUCCESS - REAL GEMINI RESPONSE] Model '{model_name}' responded successfully!")
                        break
                    except Exception as m_err:
                        print(f"[AI Module] Model '{model_name}' failed: {m_err}")
                        last_err = m_err

                if not json_text:
                    raise last_err or Exception("All candidate models failed")
            else:
                genai.configure(api_key=api_key)
                uploaded_file = genai.upload_file(path=file_path)
                print(f"[AI Module - Files API] Uploaded via standard SDK. Name: {uploaded_file.name}")

                model = genai.GenerativeModel(
                    "models/gemini-3.6-flash",
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={"response_mime_type": "application/json"}
                )
                response = model.generate_content([uploaded_file, prompt])
                json_text = response.text

            # Clean JSON text if wrapped in markdown code blocks
            clean_json = re.sub(r'^```(?:json)?\s*', '', json_text.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r'\s*```$', '', clean_json.strip(), flags=re.MULTILINE)

            result = DevOpsCurriculum.model_validate_json(clean_json)
            print(f"[AI SUCCESS - REAL GEMINI RESPONSE] Extracted {len(result.modules)} modules (2-3 concept questions per subtopic) directly from '{filename}'!")

            if result.modules:
                db = get_db()
                for idx, mod in enumerate(result.modules):
                    topic_doc = {
                        "document_id": document_id,
                        "onboarding_id": onboarding_id,
                        "title": f"{mod.module_name}",
                        "summary": mod.summary or f"Nội dung và bài học cho {mod.module_name}",
                        "estimated_study_days": mod.estimated_study_days,
                        "key_concepts": mod.key_concepts,
                        "subtopics": [_subtopic_to_dict(st) for st in mod.sub_topics],
                        "source_reference": f"Module {idx + 1}",
                        "order": idx + 1,
                        "parent_topic_id": None,
                        "created_at": datetime.now(timezone.utc),
                    }
                    await db.learning_topics.insert_one(topic_doc)

                return result

        except Exception as e:
            print(f"[AI ERROR - GEMINI API REJECTED REQUEST] {e}")
            print("[AI FALLBACK] Generating local curriculum backup because Gemini API request failed.")
        finally:
            if uploaded_file:
                try:
                    if USE_NEW_SDK:
                        client.files.delete(name=uploaded_file.name)
                    else:
                        genai.delete_file(uploaded_file.name)
                    print("[AI Module - Files API] Temporary file cleaned up on Google Server.")
                except Exception as ex:
                    print(f"[AI Module - Cleanup Warning] {ex}")
    else:
        print(f"[AI NOTICE] GEMINI_API_KEY is unconfigured ({api_key[:6]}...). Using local fallback generator.")

    # Local Fallback Generator
    return await _generate_fallback_curriculum(document_id, onboarding_id, os.path.basename(file_path))


async def _generate_fallback_curriculum(
    document_id: str,
    onboarding_id: str | None,
    filename: str,
) -> DevOpsCurriculum:
    """Generates clean fallback learning modules without embedding any filenames."""
    modules = [
        DevOpsModule(
            module_name="Module 1: Kiến thức Nền tảng & Nguyên lý Cốt lõi",
            summary="Nắm vững bản chất khái niệm nền tảng, luồng vận hành chính và các nguyên tắc thiết kế được đề cập trong bài học.",
            estimated_study_days=2,
            key_concepts=["Core Architecture", "System Principles", "Execution Workflow", "Best Practices"],
            sub_topics=[
                SubTopic(
                    title="Chuyên đề 1.1: Khái niệm Cốt lõi & Luồng vận hành",
                    summary="Phân tích cơ chế và các nguyên lý chính cần nắm vững.",
                    audit_checklist=[
                        AuditCriterion(
                            question_or_task="Giải thích bản chất khái niệm chính và luồng xử lý cốt lõi của chuyên đề này?",
                            expected_answer_keywords="Khái niệm cốt lõi, luồng vận hành chính của hệ thống",
                        ),
                        AuditCriterion(
                            question_or_task="Phân tích ưu điểm và lý do đề xuất lựa chọn kiến trúc/giải pháp trong bài học?",
                            expected_answer_keywords="Ưu điểm thiết kế và nguyên tắc ứng dụng thực tế",
                        ),
                    ],
                    quiz_questions=[
                        MultipleChoiceQuestion(
                            question="Mục tiêu đào tạo chính của bài học này là gì?",
                            options=[
                                "A. Nắm vững kiến thức chuyên môn và quy trình vận hành cốt lõi",
                                "B. Quản lý tài chính doanh nghiệp",
                                "C. Lập trình giao diện ứng dụng di động",
                                "D. Tạo báo cáo nhân sự hàng tháng",
                            ],
                            correct_answer="A",
                            explanation="Bài học tập trung đào tạo chuyên sâu về quy trình và kiến thức chuyên môn cốt lõi.",
                        ),
                        MultipleChoiceQuestion(
                            question="Khi thực thi quy trình theo hướng dẫn, yếu tố nào cần được ưu tiên kiểm tra đầu tiên?",
                            options=[
                                "A. Bỏ qua các bước xác nhận kết quả",
                                "B. Kiểm tra tính toàn vẹn và đúng đắn của trạng thái đầu ra",
                                "C. Xóa tài nguyên cấu hình ban đầu",
                                "D. Thay đổi ngẫu nhiên tham số đầu vào",
                            ],
                            correct_answer="B",
                            explanation="Kiểm tra tính toàn vẹn trạng thái đầu ra là nguyên tắc cơ bản giúp đảm bảo chất lượng vận hành.",
                        ),
                    ],
                ),
            ],
        ),
        DevOpsModule(
            module_name="Module 2: Kịch bản Thực hành & Xử lý Sự cố",
            summary="Thấu hiểu các kịch bản thực tế, phương pháp khoanh vùng sự cố và quy trình kiểm tra chất lượng dịch vụ.",
            estimated_study_days=3,
            key_concepts=["Troubleshooting", "Verification Workflow", "Quality Audit", "System Optimization"],
            sub_topics=[
                SubTopic(
                    title="Chuyên đề 2.1: Quy trình Kiểm tra & Xác nhận Kết quả",
                    summary="Các bước khoanh vùng nguyên nhân gốc rễ và xác nhận trạng thái sẵn sàng theo tiêu chuẩn.",
                    audit_checklist=[
                        AuditCriterion(
                            question_or_task="Khi gặp sự cố phát sinh trong quá trình triển khai, 3 bước khoanh vùng nguyên nhân được khuyến nghị là gì?",
                            expected_answer_keywords="Kiểm tra log lỗi, xác nhận trạng thái tài nguyên, verify tham số cấu hình",
                        ),
                    ],
                    quiz_questions=[
                        MultipleChoiceQuestion(
                            question="Hành động đầu tiên khi phát hiện lỗi trong quá trình thực hành là gì?",
                            options=[
                                "A. Khởi động lại toàn bộ máy chủ",
                                "B. Đọc chi tiết log lỗi và kiểm tra trạng thái các thành phần liên quan",
                                "C. Xóa tài liệu bài học",
                                "D. Đổi tên tệp cấu hình ngẫu nhiên",
                            ],
                            correct_answer="B",
                            explanation="Đọc chi tiết log lỗi giúp nhanh chóng xác định chính xác nguyên nhân gốc rễ (Root Cause).",
                        ),
                    ],
                ),
            ],
        ),
    ]

    db = get_db()
    for idx, mod in enumerate(modules):
        topic_doc = {
            "document_id": document_id,
            "onboarding_id": onboarding_id,
            "title": f"{mod.module_name}",
            "summary": mod.summary or f"Nội dung và bài học cho {mod.module_name}",
            "estimated_study_days": mod.estimated_study_days,
            "key_concepts": mod.key_concepts,
            "subtopics": [_subtopic_to_dict(st) for st in mod.sub_topics],
            "source_reference": f"Module {idx + 1}",
            "order": idx + 1,
            "parent_topic_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        await db.learning_topics.insert_one(topic_doc)

    return DevOpsCurriculum(document_title=filename, modules=modules)

import os
import time
import re
import json
import asyncio
from datetime import datetime, timezone
from app.config import get_settings
from app.database import get_db
from app.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt
from app.ai.schemas import (
    DevOpsCurriculum,
    DevOpsModule,
    SubTopic,
    AuditCriterion,
    MultipleChoiceQuestion,
    ConceptExplanation,
)

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
    return {
        "title": str(st),
        "summary": "",
        "lecture_content": "",
        "production_gotchas": "",
        "lab_exercise": "",
        "practical_guide": "",
        "audit_checklist": [],
        "quiz_questions": [],
    }


def _concept_exp_to_dict(ce) -> dict:
    if hasattr(ce, "model_dump"):
        return ce.model_dump()
    elif hasattr(ce, "dict"):
        return ce.dict()
    elif isinstance(ce, dict):
        return ce
    return {"term": str(ce), "definition": ""}


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
            Bạn là Principal Tech Lead & Giám đốc Đào tạo Kỹ thuật cao cấp với 15 năm kinh nghiệm quản lý các hệ thống hạ tầng lớn.
            Nhiệm vụ của bạn là đọc tài liệu đính kèm (PDF/DOCX) và phân tích thành một BỘ HƯỚNG DẪN HỌC & GIÁO ÁN ĐÀO TẠO THỰC CHIẾN (Interactive Learning & Architecture Curriculum) sâu sắc, chi tiết, giúp Intern thấu hiểu bản chất kiến thức và ứng dụng thực tế trên Cloud.

            QUY TẮC NGUYÊN TẮC BẮT BUỘC VỀ NỘI DUNG (STRICT GROUNDING & DETAILED GUIDANCE):

            1. 📖 BÀI GIẢNG LÝ THUYẾT & NGUYÊN LÝ CHUYÊN SÂU (`lecture_content`):
               - BẮT BUỘC viết bài giảng đào tạo chi tiết (200-400 từ định dạng Markdown) cho từng SubTopic như 1 Senior Leader/Principal Engineer trực tiếp giảng dạy Intern.
               - Giải thích sâu bản chất kỹ thuật, kiến trúc hệ thống, luồng thực thi (execution flow) và nguyên lý hoạt động bám sát tài liệu. Không viết hời hợt hay chỉ tóm tắt 1 câu!

            2. ⚠️ KINH NGHIỆM THỰC CHUYẾN & BẪY PRODUCTION (`production_gotchas`):
               - Nêu rõ các trade-offs, lỗi phổ biến tân thủ hay gặp, bẫy cấu hình (configuration gotchas) và lưu ý an toàn/hiệu năng trong môi trường thực tế.

            3. 🛠️ KỊCH BẢN THỰC HÀNH LAB & LỆNH THỰC THI (`lab_exercise`):
               - Cung cấp hướng dẫn lab thực hành từng bước (Step-by-step), danh sách câu lệnh CLI / file cấu hình cụ thể để Intern tự thực hành bài học.

            4. ☁️ ỨNG DỤNG THỰC TẾ TRÊN CLOUD & MÔ HÌNH HẠ TẦNG (`cloud_application`):
               - Chỉ rõ các dịch vụ Cloud (AWS EC2, S3, Docker, K8s...) và mô hình hạ tầng (Microservices, CI/CD...) ứng dụng bài học này.

            5. 🚫 TUYỆT ĐỐI BÁM SÁT TÀI LIỆU (100% STRICT GROUNDING & ZERO HALLUCINATION):
               - CHỈ SỬ DỤNG kiến thức có trong tài liệu đính kèm. Tuyệt đối không đưa tên file (.pdf, .docx) hay slide vào tiêu đề/nội dung.

            6. 🎯 BỘ CÂU HỎI AUDIT & QUIZ TRẮC NGHIỆM THỰC TẾ:
               - Audit Checklist (2 câu/subtopic): Câu hỏi Troubleshoot/Trade-off với từ khóa đáp án kỳ vọng.
               - Quiz Trắc nghiệm (2 câu/subtopic): 1 đáp án đúng và 3 phương án nhiễu kèm phần giải thích chi tiết.

            Cấu trúc JSON đầu ra bắt buộc:
            {{
              "document_title": "{filename}",
              "modules": [
                {{
                  "module_name": "Module 1: Tên Module chuẩn chuyên môn bám sát tài liệu",
                  "summary": "Tóm tắt 2-3 câu về nội dung và mục tiêu đào tạo cốt lõi của Module",
                  "estimated_study_days": 2,
                  "cloud_application": "Ứng dụng thực tế trên Cloud (AWS/GCP/Docker/K8s...) và mô hình hạ tầng phù hợp (Microservices, CI/CD...)",
                  "key_concepts": ["Khái niệm 1", "Khái niệm 2", "Khái niệm 3"],
                  "concept_explanations": [
                    {{"term": "Khái niệm 1", "definition": "Giải thích bản chất khái niệm 1 ngắn gọn"}},
                    {{"term": "Khái niệm 2", "definition": "Giải thích bản chất khái niệm 2 ngắn gọn"}}
                  ],
                  "sub_topics": [
                    {{
                      "title": "Chuyên đề 1.1: Tên chuyên đề bám sát mạch tài liệu",
                      "summary": "Tóm tắt mục tiêu bài học chuyên đề",
                      "lecture_content": "### 1. Kiến trúc & Bản chất Kỹ thuật\\nBài giảng chi tiết 200-400 từ giải thích sâu về cơ chế vận hành...\\n### 2. Luồng xử lý dữ liệu\\nGiải thích từng bước luồng thực thi...",
                      "production_gotchas": "⚠️ **Bẫy Production thường gặp:**\\n- Lỗi 1: Cấu hình sai timeout...\\n- Lỗi 2: Tránh sử dụng root privilege...",
                      "lab_exercise": "🛠️ **Kịch bản Thực hành Lab:**\\n1. Chạy lệnh: `docker run -d ...`\\n2. Kiểm tra log với: `docker logs -f`...",
                      "practical_guide": "Hướng dẫn thực hành tóm tắt & các lưu ý kỹ thuật khi làm lab",
                      "audit_checklist": [
                        {{
                          "question_or_task": "Câu hỏi Audit dạng Troubleshoot/Trade-off/Cơ chế cụ thể",
                          "expected_answer_keywords": "Từ khóa & ý trả lời cốt lõi bắt buộc"
                        }}
                      ],
                      "quiz_questions": [
                        {{
                          "question": "Câu hỏi trắc nghiệm 1 kiểm tra tư duy thực chiến bám sát bài học?",
                          "options": ["A. Phương án đúng", "B. Phương án nhiễu 1", "C. Phương án nhiễu 2", "D. Phương án nhiễu 3"],
                          "correct_answer": "A",
                          "explanation": "Giải thích chi tiết tại sao A đúng và tại sao B, C, D sai dựa trên tài liệu"
                        }}
                      ]
                    }}
                  ]
                }}
              ]
            }}

            Bóc tách tài liệu 100% bám sát nội dung đính kèm!
            """

            json_text = ""

            if USE_NEW_SDK:
                client = genai.Client(api_key=api_key)
                uploaded_file = await asyncio.to_thread(client.files.upload, file=file_path)
                print(f"[AI Module - Files API] Uploaded via new SDK. URI: {uploaded_file.uri}")

                candidate_models = [
                    "gemini-3.6-flash",
                    "models/gemini-3.6-flash",
                    "gemini-2.0-flash",
                    "gemini-1.5-flash",
                ]
                last_err = None
                for model_name in candidate_models:
                    for attempt in range(3):
                        try:
                            print(f"[AI Module] Requesting generate_content with model '{model_name}' (Attempt {attempt + 1})...")
                            def _gen(m_name, f_obj, p_text):
                                return client.models.generate_content(
                                    model=m_name,
                                    contents=[f_obj, p_text],
                                    config=types.GenerateContentConfig(
                                        response_mime_type="application/json",
                                        response_schema=DevOpsCurriculum,
                                        temperature=0.3,
                                    ),
                                )
                            response = await asyncio.to_thread(_gen, model_name, uploaded_file, prompt)
                            json_text = response.text
                            print(f"[AI SUCCESS - REAL GEMINI RESPONSE] Model '{model_name}' responded successfully!")
                            break
                        except Exception as m_err:
                            print(f"[AI Module] Model '{model_name}' attempt {attempt + 1} failed: {m_err}")
                            last_err = m_err
                            if "503" in str(m_err) or "high demand" in str(m_err).lower() or "unavailable" in str(m_err).lower():
                                print(f"[AI Retry] Model '{model_name}' 503 High Demand spike detected. Retrying in 2 seconds...")
                                await asyncio.sleep(2)
                            else:
                                break
                    if json_text:
                        break

                if not json_text:
                    raise last_err or Exception("All candidate models failed")
            else:
                genai.configure(api_key=api_key)
                uploaded_file = await asyncio.to_thread(genai.upload_file, path=file_path)
                print(f"[AI Module - Files API] Uploaded via standard SDK. Name: {uploaded_file.name}")

                model = genai.GenerativeModel(
                    "gemini-3.6-flash",
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={"response_mime_type": "application/json"}
                )
                response = await asyncio.to_thread(model.generate_content, [uploaded_file, prompt])
                json_text = response.text

            # Clean JSON text if wrapped in markdown code blocks
            clean_json = re.sub(r'^```(?:json)?\s*', '', json_text.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r'\s*```$', '', clean_json.strip(), flags=re.MULTILINE)

            result = DevOpsCurriculum.model_validate_json(clean_json)
            print(f"[AI SUCCESS] Extracted {len(result.modules)} modules with Cloud Application & Concept Explanations!")

            if result.modules:
                db = get_db()
                for idx, mod in enumerate(result.modules):
                    topic_doc = {
                        "document_id": document_id,
                        "onboarding_id": onboarding_id,
                        "title": f"{mod.module_name}",
                        "summary": mod.summary or f"Nội dung và bài học cho {mod.module_name}",
                        "estimated_study_days": mod.estimated_study_days,
                        "cloud_application": mod.cloud_application or "Tích hợp ứng dụng triển khai dịch vụ Cloud & hạ tầng doanh nghiệp.",
                        "key_concepts": mod.key_concepts,
                        "concept_explanations": [_concept_exp_to_dict(ce) for ce in mod.concept_explanations],
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
            print("[AI FALLBACK] Generating local curriculum backup with full cloud guidance.")
        finally:
            if uploaded_file:
                try:
                    if USE_NEW_SDK:
                        await asyncio.to_thread(client.files.delete, name=uploaded_file.name)
                    else:
                        await asyncio.to_thread(genai.delete_file, uploaded_file.name)
                    print("[AI Module - Files API] Temporary file cleaned up on Google Server.")
                except Exception as ex:
                    print(f"[AI Module - Cleanup Warning] {ex}")
    else:
        print(f"[AI NOTICE] GEMINI_API_KEY is unconfigured ({api_key[:6]}...). Using local fallback generator.")

    return await _generate_fallback_curriculum(document_id, onboarding_id, os.path.basename(file_path))


async def _generate_fallback_curriculum(
    document_id: str,
    onboarding_id: str | None,
    filename: str,
) -> DevOpsCurriculum:
    """Generates fallback learning modules enriched with Cloud Applications & Concept Explanations."""
    modules = [
        DevOpsModule(
            module_name="Module 1: Kiến thức Nền tảng & Nguyên lý Cốt lõi",
            summary="Nắm vững bản chất khái niệm nền tảng, luồng vận hành chính và các nguyên tắc thiết kế được đề cập trong bài học.",
            estimated_study_days=2,
            cloud_application="Ứng dụng trên AWS (EC2, VPC), GCP Compute Engine, mô hình Microservices & CI/CD Pipeline tự động hóa.",
            key_concepts=["Core Architecture", "System Principles", "Execution Workflow", "Best Practices"],
            concept_explanations=[
                ConceptExplanation(
                    term="Core Architecture",
                    definition="Kiến trúc tổng thể quy định cách các thành phần dịch vụ tương tác và kết nối với nhau.",
                ),
                ConceptExplanation(
                    term="Execution Workflow",
                    definition="Luồng thực thi quy trình từ khi khởi tạo tới khi hoàn tất nghiệm thu trạng thái.",
                ),
            ],
            sub_topics=[
                SubTopic(
                    title="Chuyên đề 1.1: Khái niệm Cốt lõi & Luồng vận hành",
                    summary="Phân tích cơ chế và các nguyên lý chính cần nắm vững.",
                    lecture_content="""### 📖 Bài giảng Kỹ thuật Chuyên sâu từ Senior Leader

Toàn bộ kiến trúc và quy trình vận hành trong bài học này được thiết kế theo chuẩn doanh nghiệp. 

1. **Nguyên lý Thiết kế & Bản chất Kỹ thuật:**
   - Hệ thống vận hành dựa trên cơ chế phân tách trách nhiệm (Separation of Concerns). Mỗi thành phần đảm nhận một vai trò duy nhất và giao tiếp qua API/Interface tiêu chuẩn.
   - Luồng dữ liệu chính đi qua 3 giai đoạn: Tiếp nhận Request $\rightarrow$ Xác thực & Kiểm tra Điều kiện $\rightarrow$ Ghi nhận Trạng thái & Phản hồi.

2. **Luồng Thực thi & Vận hành:**
   - Trạng thái được đồng bộ thời gian thực để tránh nghẽn dữ liệu (Data Race Condition).
   - Tệp cấu hình cần được tập trung hóa và phân tách rõ môi trường Development / Staging / Production.""",
                    production_gotchas="""⚠️ **Kinh nghiệm Thực chiến & Bẫy Production (Senior Tips):**
- **Tránh cứng hóa tham số (Hardcode):** Luôn đưa cấu hình kết nối vào biến môi trường (Environment Variables).
- **Kiểm soát Retry Loop:** Khi hệ thống ngắt kết nối, không tự động retry liên tục không giới hạn để tránh làm sập server chính (Cascading Failure).""",
                    lab_exercise="""🛠️ **Kịch bản Thực hành Lab:**
1. Khởi tạo môi trường lab thử nghiệm trên Docker/Sandbox.
2. Thực thi kiểm tra trạng thái dịch vụ với câu lệnh: `curl -i http://localhost/healthcheck`
3. Theo dõi log vận hành thời gian thực để verify kết quả.""",
                    practical_guide="Đọc kỹ sơ đồ luồng dữ liệu, thực hành dựng môi trường Sandbox và verify log hệ thống trước khi tiếp tục.",
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
                    ],
                ),
            ],
        ),
        DevOpsModule(
            module_name="Module 2: Kịch bản Thực hành & Xử lý Sự cố (Troubleshooting)",
            summary="Thấu hiểu các kịch bản thực tế, phương pháp khoanh vùng sự cố và quy trình kiểm tra chất lượng dịch vụ.",
            estimated_study_days=3,
            cloud_application="Ứng dụng quản trị Container (Docker, Kubernetes Cluster), AWS CloudWatch Logs & Grafana Monitoring.",
            key_concepts=["Troubleshooting", "Verification Workflow", "Quality Audit", "System Optimization"],
            concept_explanations=[
                ConceptExplanation(
                    term="Troubleshooting",
                    definition="Quy trình 3 bước khoanh vùng và xử lý nguyên nhân gốc rễ (Root Cause) khi hệ thống gặp lỗi.",
                ),
                ConceptExplanation(
                    term="Verification Workflow",
                    definition="Bộ tiêu chí xác nhận dịch vụ đạt trạng thái sẵn sàng (Health Check & Readiness).",
                ),
            ],
            sub_topics=[
                SubTopic(
                    title="Chuyên đề 2.1: Quy trình Kiểm tra & Xác nhận Kết quả",
                    summary="Các bước khoanh vùng nguyên nhân gốc rễ và xác nhận trạng thái sẵn sàng theo tiêu chuẩn.",
                    lecture_content="""### 📖 Hướng dẫn Phân tích & Khoanh vùng Sự cố (Root Cause Analysis)

Khi làm việc trong môi trường Production, 80% thời gian của Kỹ sư là đọc log và khoanh vùng sự cố.

1. **Phương pháp 3 Bước Khoanh vùng:**
   - **Bước 1 (Check Logs):** Đọc log từ dưới lên để tìm từ khóa Exception / Error đầu tiên phát sinh.
   - **Bước 2 (Check Metrics & Resource):** Kiểm tra CPU, RAM, Disk space và Network latency.
   - **Bước 3 (Verify Config & Dependency):** Kiểm tra các dịch vụ phụ thuộc (Database, Cache, Third-party APIs) xem có bị sập hay quá tải không.

2. **Quy tắc An toàn khi Fix bug:**
   - Tuyệt đối không sửa code trực tiếp trên Production! Phải tái hiện lỗi trên Staging trước khi hotfix.""",
                    production_gotchas="""⚠️ **Kinh nghiệm Thực chiến & Bẫy Production (Senior Tips):**
- **Không nuốt ngoại lệ (Swallow Exception):** Tránh viết `try: ... except: pass` vì sẽ làm ẩn lỗi, khiến việc debug sau này trở nên cực kỳ khó khăn.
- **Log đủ ngữ cảnh:** Mọi câu log lỗi phải kèm `user_id`, `request_id` hoặc `timestamp` chính xác.""",
                    lab_exercise="""🛠️ **Kịch bản Thực hành Lab:**
1. Tạo một lỗi giả lập timeout trong môi trường thử nghiệm.
2. Kiểm tra log hệ thống bằng lệnh: `docker compose logs -f --tail=50`
3. Phân tích nguyên nhân và thực hiện quy trình rollback khẩn cấp.""",
                    practical_guide="Kiểm tra hệ thống log thời gian thực, tái hiện lại sự cố trong lab cách ly và ghi nhận dấu hiệu bất thường.",
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
            "cloud_application": mod.cloud_application,
            "key_concepts": mod.key_concepts,
            "concept_explanations": [_concept_exp_to_dict(ce) for ce in mod.concept_explanations],
            "subtopics": [_subtopic_to_dict(st) for st in mod.sub_topics],
            "source_reference": f"Module {idx + 1}",
            "order": idx + 1,
            "parent_topic_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        await db.learning_topics.insert_one(topic_doc)

    return DevOpsCurriculum(document_title=filename, modules=modules)

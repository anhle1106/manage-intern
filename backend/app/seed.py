import asyncio
from datetime import datetime, timezone
from app.database import connect_db, close_db, get_db
from app.auth.service import hash_password
from app.common.enums import Role, LeaveType, LeaveStatus, OnboardingStatus, ProcessingStatus


async def seed_data():
    await connect_db()
    db = get_db()

    print("Cleaning existing database...")
    await db.users.delete_many({})
    await db.intern_profiles.delete_many({})
    await db.schedules.delete_many({})
    await db.leave_requests.delete_many({})
    await db.onboardings.delete_many({})
    await db.documents.delete_many({})
    await db.learning_topics.delete_many({})
    await db.learning_progress.delete_many({})

    print("Creating users...")
    now = datetime.now(timezone.utc)
    password_hash = hash_password("1")
    leader_hash = hash_password("1")
    intern_hash = hash_password("1")

    # 1. Admin
    admin_res = await db.users.insert_one({
        "email": "admin@devops.com",
        "hashed_password": password_hash,
        "full_name": "System Administrator",
        "role": Role.ADMIN.value,
        "is_active": True,
        "created_at": now,
    })
    admin_id = str(admin_res.inserted_id)

    # 2. Leaders
    l1_res = await db.users.insert_one({
        "email": "leader1@devops.com",
        "hashed_password": leader_hash,
        "full_name": "Alex Tech Lead",
        "role": Role.LEADER.value,
        "is_active": True,
        "created_at": now,
    })
    l1_id = str(l1_res.inserted_id)

    l2_res = await db.users.insert_one({
        "email": "leader2@devops.com",
        "hashed_password": leader_hash,
        "full_name": "Sarah DevOps Mentor",
        "role": Role.LEADER.value,
        "is_active": True,
        "created_at": now,
    })
    l2_id = str(l2_res.inserted_id)

    # 3. Interns
    interns_data = [
        ("intern1@devops.com", "John Doe", "Hanoi University of Science & Tech", "Computer Engineering", "20210001", "0912345671"),
        ("intern2@devops.com", "Jane Smith", "National Economics University", "Information Systems", "20210002", "0912345672"),
        ("intern3@devops.com", "Bob Johnson", "VNU University of Engineering", "Computer Science", "20210003", "0912345673"),
        ("intern4@devops.com", "Alice Williams", "Post and Telecom Institute", "Telecommunications", "20210004", "0912345674"),
        ("intern5@devops.com", "Charlie Brown", "FPT University", "Software Engineering", "20210005", "0912345675"),
    ]

    intern_ids = []
    for email, name, uni, major, st_id, phone in interns_data:
        res = await db.users.insert_one({
            "email": email,
            "hashed_password": intern_hash,
            "full_name": name,
            "role": Role.INTERN.value,
            "is_active": True,
            "created_at": now,
        })
        iid = str(res.inserted_id)
        intern_ids.append(iid)

        await db.intern_profiles.insert_one({
            "user_id": iid,
            "university": uni,
            "major": major,
            "student_id": st_id,
            "phone": phone,
            "start_date": "2026-06-01",
            "created_at": now,
        })

    print("Creating onboarding batch...")
    onboarding_res = await db.onboardings.insert_one({
        "name": "DevOps Intern K12",
        "description": "Summer 2026 DevOps Engineering Onboarding Program covering Linux, Docker, K8s & CI/CD.",
        "start_date": "2026-06-01",
        "end_date": "2026-09-01",
        "status": OnboardingStatus.ACTIVE.value,
        "leader_ids": [l1_id, l2_id],
        "intern_ids": intern_ids,
        "created_at": now,
    })
    batch_id = str(onboarding_res.inserted_id)

    print("Creating sample university schedules...")
    sample_schedules = [
        # intern1
        {"user_id": intern_ids[0], "subject": "Computer Networks", "day_of_week": 0, "start_time": "07:00", "end_time": "09:00", "location": "Room A101", "note": "Bring laptop", "start_date": "2026-05-01", "end_date": "2026-09-30"},
        {"user_id": intern_ids[0], "subject": "Operating Systems", "day_of_week": 2, "start_time": "09:30", "end_time": "11:30", "location": "Lab B202", "note": "Linux lab", "start_date": "2026-05-01", "end_date": "2026-09-30"},
        # intern2
        {"user_id": intern_ids[1], "subject": "Database Systems", "day_of_week": 1, "start_time": "08:00", "end_time": "10:00", "location": "Hall C303", "note": "", "start_date": "2026-05-01", "end_date": "2026-09-30"},
        {"user_id": intern_ids[1], "subject": "Software Architecture", "day_of_week": 3, "start_time": "13:00", "end_time": "15:00", "location": "Room D404", "note": "", "start_date": "2026-05-01", "end_date": "2026-09-30"},
    ]
    for s in sample_schedules:
        s["created_at"] = now
        await db.schedules.insert_one(s)

    print("Creating sample leave requests...")
    sample_leaves = [
        {"user_id": intern_ids[0], "leave_type": LeaveType.UNIVERSITY.value, "start_datetime": "2026-09-10T08:00:00Z", "end_datetime": "2026-09-10T12:00:00Z", "reason": "Midterm exam for Computer Networks", "status": LeaveStatus.PENDING.value, "reviewed_by": None, "reviewed_at": None, "created_at": now},
        {"user_id": intern_ids[1], "leave_type": LeaveType.SICK.value, "start_datetime": "2026-08-20T08:00:00Z", "end_datetime": "2026-08-20T17:00:00Z", "reason": "Doctor appointment", "status": LeaveStatus.APPROVED.value, "reviewed_by": l1_id, "reviewed_at": now, "created_at": now},
        {"user_id": intern_ids[2], "leave_type": LeaveType.PERSONAL.value, "start_datetime": "2026-08-25T08:00:00Z", "end_datetime": "2026-08-25T17:00:00Z", "reason": "Family event", "status": LeaveStatus.REJECTED.value, "reviewed_by": l1_id, "reviewed_at": now, "created_at": now},
    ]
    for l in sample_leaves:
        await db.leave_requests.insert_one(l)

    print("Creating sample document and learning topics...")
    doc_res = await db.documents.insert_one({
        "filename": "AWS_DevOps_Fundamentals.pdf",
        "file_type": "pdf",
        "file_size": 2048500,
        "cloudinary_url": "https://res.cloudinary.com/demo/image/upload/v1631234567/sample.pdf",
        "cloudinary_public_id": "sample_pdf",
        "uploaded_by": admin_id,
        "onboarding_id": batch_id,
        "processing_status": ProcessingStatus.COMPLETED.value,
        "extracted_text": "AWS DevOps Fundamentals Sample Text...",
        "created_at": now,
    })
    doc_id = str(doc_res.inserted_id)

    sample_topics = [
        {
            "document_id": doc_id,
            "onboarding_id": batch_id,
            "title": "1. AWS Overview & Core Services",
            "summary": "Introduction to Amazon Web Services, global infrastructure, region & availability zones.",
            "key_concepts": ["Region", "Availability Zone", "Edge Location", "AWS Management Console"],
            "subtopics": [
                {"title": "Global Infrastructure", "summary": "Understanding Regions and AZs"},
                {"title": "Shared Responsibility Model", "summary": "Security of the cloud vs in the cloud"}
            ],
            "source_reference": "Section 1",
            "order": 1,
            "created_at": now,
        },
        {
            "document_id": doc_id,
            "onboarding_id": batch_id,
            "title": "2. IAM (Identity & Access Management)",
            "summary": "Securely manage access to AWS services and resources using Users, Groups, Roles, and Policies.",
            "key_concepts": ["IAM User", "IAM Group", "IAM Role", "JSON Policy", "MFA"],
            "subtopics": [
                {"title": "Users & Groups", "summary": "Managing human and programmatic identities"},
                {"title": "Roles & Policies", "summary": "Granting temporary credentials and least privilege principle"}
            ],
            "source_reference": "Section 2",
            "order": 2,
            "created_at": now,
        },
        {
            "document_id": doc_id,
            "onboarding_id": batch_id,
            "title": "3. Amazon EC2 & Storage",
            "summary": "Virtual servers in the cloud, Elastic Block Store (EBS), and Amazon S3 object storage.",
            "key_concepts": ["EC2 Instance", "AMI", "EBS Volume", "S3 Bucket", "Security Group"],
            "subtopics": [
                {"title": "EC2 Lifecycle", "summary": "Instance types, pricing models, and security groups"},
                {"title": "S3 & EBS", "summary": "Block storage vs object storage"}
            ],
            "source_reference": "Section 3",
            "order": 3,
            "created_at": now,
        },
        {
            "document_id": doc_id,
            "onboarding_id": batch_id,
            "title": "4. VPC (Virtual Private Cloud)",
            "summary": "Isolated cloud network, subnets, route tables, internet gateways, and NAT gateways.",
            "key_concepts": ["VPC", "Public Subnet", "Private Subnet", "Internet Gateway", "Route Table"],
            "subtopics": [
                {"title": "Subnets & Routing", "summary": "Public vs private subnet routing"},
                {"title": "Security & Network ACLs", "summary": "Security Groups vs Network ACLs"}
            ],
            "source_reference": "Section 4",
            "order": 4,
            "created_at": now,
        },
    ]

    topic_ids = []
    for t in sample_topics:
        res = await db.learning_topics.insert_one(t)
        topic_ids.append(str(res.inserted_id))

    print("Creating sample progress for interns...")
    # Intern 1 completed topics 1 & 2
    await db.learning_progress.insert_one({"user_id": intern_ids[0], "topic_id": topic_ids[0], "completed": True, "completed_at": now})
    await db.learning_progress.insert_one({"user_id": intern_ids[0], "topic_id": topic_ids[1], "completed": True, "completed_at": now})

    # Intern 2 completed topic 1
    await db.learning_progress.insert_one({"user_id": intern_ids[1], "topic_id": topic_ids[0], "completed": True, "completed_at": now})

    print("Seed data completed successfully!")
    await close_db()


if __name__ == "__main__":
    asyncio.run(seed_data())

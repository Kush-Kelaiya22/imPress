import asyncio
from app.database import async_session
from app.models import Student, User, ClassSession, EspDevice
from sqlalchemy import select

async def main():
    async with async_session() as db:
        r = await db.execute(select(Student))
        for s in r.scalars().all():
            print(f'Student: id={s.id}, roll={s.roll_number}, name={s.student_name}')
        r = await db.execute(select(User))
        for u in r.scalars().all():
            print(f'User: id={u.id}, username={u.username}, email={u.email}, role={u.role}')
        r = await db.execute(select(ClassSession))
        for c in r.scalars().all():
            print(f'Class: id={c.id}, name={c.name}, code={c.code}, teacher_id={c.teacher_id}, device_id={c.device_id}')
        r = await db.execute(select(EspDevice))
        for d in r.scalars().all():
            print(f'Device: id={d.id}, mac={d.mac_address}, type={d.device_type}, name={d.device_name}, class={d.class_session_id}, connected={d.is_connected}')
asyncio.run(main())
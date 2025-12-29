import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.sql import func
from datetime import datetime, timedelta

from database.models import User, Channel, UserType, AI_Token


################################ User #####################################

async def orm_add_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str | None = None,
    address: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> tuple[User, bool]:

    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        new_user = User(
            telegram_id=telegram_id,
            full_name=full_name or "No name",
            address=address or "No address",
            lat=lat,
            lon=lon,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user, True
    else:
        return existing_user, False


async def orm_update_location(
    session: AsyncSession,
    user_id: int,
    address: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
):
    user = await session.get(User, user_id)

    if not user:
        return None

    updated = False

    if address is not None:
        user.address = address
        updated = True

    if lat is not None:
        user.lat = lat
        updated = True

    if lon is not None:
        user.lon = lon
        updated = True

    if updated:
        await session.commit()
        await session.refresh(user)

    return user




async def select_user(telegram_id: int, session: AsyncSession):
    query = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(query)
    user = result.scalars().first()
    return user


async def is_user_active(telegram_id: int, session: AsyncSession) -> bool | None:
    try:
        query = select(User.is_active).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    except Exception as e:
        print(f"Xatolik: {e}")
        return None


async def select_all_users(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()


async def delete_all_users(session: AsyncSession):
    try:
        query = delete(User)
        await session.execute(query)
        await session.commit()

    except Exception as e:
        await session.rollback()
        print(f"Error deleting users: {e}")


async def count_daily_users(session: AsyncSession):
    today = datetime.now().date()
    query = select(func.count()).where(User.joined_at >= today)
    result = await session.execute(query)
    return result.scalar()


async def count_weekly_users(session: AsyncSession):
    last_week = datetime.now().date() - timedelta(days=7)
    query = select(func.count()).where(User.joined_at >= last_week)
    result = await session.execute(query)
    return result.scalar()


async def count_monthly_users(session: AsyncSession):
    last_month = datetime.now().date() - timedelta(days=30)
    query = select(func.count()).where(User.joined_at >= last_month)
    result = await session.execute(query)
    return result.scalar()


async def count_users(session: AsyncSession):
    query = select(func.count()).select_from(User)
    result = await session.execute(query)
    return result.scalar()


async def orm_admin_exist(session: AsyncSession, admin_id: int) -> bool:
    stmt = select(exists().where(User.telegram_id == admin_id))
    result = await session.execute(stmt)
    return result.scalar()


async def orm_add_admin(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    company_id: int,
    branch_id: int,
    user_type: UserType = UserType.ADMIN,   # default ADMIN
):
    new_admin = User(
        telegram_id=telegram_id,
        full_name=full_name,
        company_id=company_id,
        branch_id=branch_id,
        user_type=user_type,
        is_active=True
    )
    session.add(new_admin)

    try:
        await session.commit()
        await session.refresh(new_admin)
        return new_admin
    except IntegrityError:
        await session.rollback()
        return None


async def orm_delete_admin_by_id(session: AsyncSession, admin_id: int):
    query = delete(User).where(User.telegram_id == admin_id)
    await session.execute(query)
    await session.commit()


async def orm_delete_by_id(session: AsyncSession, telegram_id: int):
    query = delete(User).where(User.telegram_id == telegram_id)
    await session.execute(query)
    await session.commit()


######################## Channel #######################################


async def select_channel(session: AsyncSession, channel_id: int):
    query = select(Channel).where(Channel.channel_id == channel_id)
    result = await session.execute(query)
    return result.scalars().first()


async def delete_channels(session: AsyncSession):
    query = delete(Channel)
    await session.execute(query)
    await session.commit()

######################## Channel #######################################


async def save_single_token(title: str, token: str, session: AsyncSession):
    try:
        await session.execute(delete(AI_Token))
        await session.commit()

        new_token = AI_Token(
            title=title,
            token=token,
            count=0
        )

        session.add(new_token)
        await session.commit()
        await session.refresh(new_token)

        return new_token

    except Exception as e:
        await session.rollback()
        raise e


async def get_single_token(session: AsyncSession) -> AI_Token | None:
    query = await session.execute(select(AI_Token))
    return query.scalar_one_or_none()


async def update_single_token(
    token_id: int,
    session: AsyncSession,
    title: str = None,
    token: str = None
):
    query = await session.execute(select(AI_Token).where(AI_Token.id == token_id))
    token_obj = query.scalar_one_or_none()

    if not token_obj:
        return None

    if title is not None:
        token_obj.title = title

    if token is not None and token != token_obj.token:
        token_obj.token = token
        token_obj.count = 0

    await session.commit()
    await session.refresh(token_obj)

    return token_obj


async def delete_ai_token(session: AsyncSession, token_id: int) -> bool:
    result = await session.execute(
        select(AI_Token).where(AI_Token.id == token_id)
    )
    token_obj = result.scalar_one_or_none()

    if not token_obj:
        return False

    await session.delete(token_obj)
    await session.commit()

    return True


async def increment_token_count(session: AsyncSession, token_id: int):
    await session.execute(
        update(AI_Token)
        .where(AI_Token.id == token_id)
        .values(count=AI_Token.count + 1)
    )
    await session.commit()

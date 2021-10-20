from datetime import datetime
from typing import List, Optional, Union
from lnbits.helpers import urlsafe_short_hash

from . import db
from .models import WithdrawLink, HashCheck


async def create_withdraw_link(
    *,
    wallet_id: str,
    title: str,
    currency: str,
    amount: float,
) -> WithdrawLink:
    link_id = urlsafe_short_hash()
    await db.execute(
        """
        INSERT INTO withdrawfiat.withdraw_link (
            id,
            wallet,
            title,
            currency,
            amount,
            unique_hash,
            k1
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            link_id,
            wallet_id,
            title,
            currency,
            amount,
            urlsafe_short_hash(),
            urlsafe_short_hash(),
        ),
    )
    link = await get_withdraw_link(link_id)
    assert link, "Newly created link couldn't be retrieved"
    return link


async def get_withdraw_link(link_id: str) -> Optional[WithdrawLink]:
    row = await db.fetchone(
        "SELECT * FROM withdrawfiat.withdraw_link WHERE id = ?", (link_id,)
    )
    if not row:
        return None

    link = []
    for item in row:
        link.append(item)
    return WithdrawLink._make(link)


async def get_withdraw_link_by_hash(unique_hash: str) -> Optional[WithdrawLink]:
    row = await db.fetchone(
        "SELECT * FROM withdrawfiat.withdraw_link WHERE unique_hash = ?", (unique_hash,)
    )
    if not row:
        return None

    link = []
    for item in row:
        link.append(item)
    return WithdrawLink._make(link)


async def get_withdraw_links(wallet_ids: Union[str, List[str]]) -> List[WithdrawLink]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]

    q = ",".join(["?"] * len(wallet_ids))
    rows = await db.fetchall(
        f"SELECT * FROM withdrawfiat.withdraw_link WHERE wallet IN ({q})", (*wallet_ids,)
    )

    return [WithdrawLink.from_row(row) for row in rows]


async def update_withdraw_link(link_id: str, **kwargs) -> Optional[WithdrawLink]:
    q = ", ".join([f"{field[0]} = ?" for field in kwargs.items()])
    await db.execute(
        f"UPDATE withdrawfiat.withdraw_link SET {q} WHERE id = ?",
        (*kwargs.values(), link_id),
    )
    row = await db.fetchone(
        "SELECT * FROM withdrawfiat.withdraw_link WHERE id = ?", (link_id,)
    )
    return WithdrawLink.from_row(row) if row else None


async def delete_withdraw_link(link_id: str) -> None:
    await db.execute("DELETE FROM withdrawfiat.withdraw_link WHERE id = ?", (link_id,))


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def create_hash_check(
    the_hash: str,
    lnurl_id: str,
) -> HashCheck:
    await db.execute(
        """
        INSERT INTO withdrawfiat.hash_check (
            id,
            lnurl_id
        )
        VALUES (?, ?)
        """,
        (
            the_hash,
            lnurl_id,
        ),
    )
    hashCheck = await get_hash_check(the_hash, lnurl_id)
    return hashCheck


async def get_hash_check(the_hash: str, lnurl_id: str) -> Optional[HashCheck]:
    rowid = await db.fetchone(
        "SELECT * FROM withdrawfiat.hash_check WHERE id = ?", (the_hash,)
    )
    rowlnurl = await db.fetchone(
        "SELECT * FROM withdrawfiat.hash_check WHERE lnurl_id = ?", (lnurl_id,)
    )
    if not rowlnurl:
        await create_hash_check(the_hash, lnurl_id)
        return {"lnurl": True, "hash": False}
    else:
        if not rowid:
            await create_hash_check(the_hash, lnurl_id)
            return {"lnurl": True, "hash": False}
        else:
            return {"lnurl": True, "hash": True}

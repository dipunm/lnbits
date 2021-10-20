async def m001_initial(db):
    """
    Creates a withdraw table
    """
    await db.execute(
        """
        CREATE TABLE withdrawfiat.withdraw_link (
            id TEXT PRIMARY KEY,
            wallet TEXT,
            title TEXT,
            currency TEXT NOT NULL,
            amount FLOAT NOT NULL,
            max_satoshis INTEGER DEFAULT 0,
            unique_hash TEXT UNIQUE,
            k1 TEXT,
            used INTEGER DEFAULT 0,
            settled_msats INTEGER
        );
        """
    )


async def m003_make_hash_check(db):
    """
    Creates a hash check table.
    """
    await db.execute(
        """
        CREATE TABLE withdrawfiat.hash_check (
            id TEXT PRIMARY KEY,
            lnurl_id TEXT
        );
    """
    )

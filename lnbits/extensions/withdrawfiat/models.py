from lnbits.utils.exchange_rates import fiat_amount_as_satoshis
from quart import url_for
from lnurl import Lnurl, LnurlWithdrawResponse, encode as lnurl_encode  # type: ignore
from sqlite3 import Row
from typing import NamedTuple


class WithdrawLink(NamedTuple):
    id: str
    wallet: str
    title: str
    currency: str
    amount: float
    max_satoshis: int
    unique_hash: str
    k1: str
    used: int
    settledMSats: int
    
    @classmethod
    def from_row(cls, row: Row) -> "WithdrawLink":
        data = dict(row)
        return cls(**data)

    @property
    def is_spent(self) -> bool:
        return self.used > 0

    @property
    def lnurl(self) -> Lnurl:
        url = url_for(
            "withdraw.api_lnurl_response",
            unique_hash=self.unique_hash,
            _external=True,
        )

        return lnurl_encode(url)

    def lnurl_response(self, sats) -> LnurlWithdrawResponse:
        url = url_for(
            "withdraw.api_lnurl_callback", unique_hash=self.unique_hash, _external=True
        )
        
        return LnurlWithdrawResponse(
            callback=url,
            k1=self.k1,
            min_withdrawable=sats * 1000,
            max_withdrawable=sats * 1000,
            default_description=self.title,
        )


class HashCheck(NamedTuple):
    id: str
    lnurl_id: str

    @classmethod
    def from_row(cls, row: Row) -> "Hash":
        return cls(**dict(row))

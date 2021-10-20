from quart import g, jsonify, request
from http import HTTPStatus
from lnurl.exceptions import InvalidUrl as LnurlInvalidUrl  # type: ignore

from lnbits.core.crud import get_user
from lnbits.decorators import api_check_wallet_key, api_validate_post_request

from . import withdrawfiat_ext
from .crud import (
    create_withdraw_link,
    get_withdraw_link,
    get_withdraw_links,
    delete_withdraw_link,
    get_hash_check,
)


@withdrawfiat_ext.route("/api/v1/links", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_links():
    wallet_ids = [g.wallet.id]

    if "all_wallets" in request.args:
        wallet_ids = (await get_user(g.wallet.user)).wallet_ids
    try:
        return (
            jsonify(
                [
                    {
                        **link._asdict(),
                        **{"lnurl": link.lnurl},
                    }
                    for link in await get_withdraw_links(wallet_ids)
                ]
            ),
            HTTPStatus.OK,
        )
    except LnurlInvalidUrl:
        return (
            jsonify(
                {
                    "message": "LNURLs need to be delivered over a publically accessible `https` domain or Tor."
                }
            ),
            HTTPStatus.UPGRADE_REQUIRED,
        )


@withdrawfiat_ext.route("/api/v1/links/<link_id>", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_link_retrieve(link_id):
    link = await get_withdraw_link(link_id)

    if not link:
        return (
            jsonify({"message": "Withdraw link does not exist."}),
            HTTPStatus.NOT_FOUND,
        )

    if link.wallet != g.wallet.id:
        return jsonify({"message": "Not your withdraw link."}), HTTPStatus.FORBIDDEN

    return jsonify({**link._asdict(), **{"lnurl": link.lnurl}}), HTTPStatus.OK


@withdrawfiat_ext.route("/api/v1/links", methods=["POST"])
@api_check_wallet_key("admin")
@api_validate_post_request(
    schema={
        "title": {"type": "string", "empty": False, "required": True},
        "currency": {"type": "string", "empty": False, "required": True},
        "amount": {"type": "float", "min": 0, "required": True},
        "max_satoshis": {"type": "integer", "min": 1, "required": True},
    }
)
async def api_link_create_or_update():
    link = await create_withdraw_link(
        wallet_id=g.wallet.id, **g.data
    )

    return (
        jsonify({**link._asdict(), **{"lnurl": link.lnurl}}),
        HTTPStatus.CREATED,
    )


@withdrawfiat_ext.route("/api/v1/links/<link_id>", methods=["DELETE"])
@api_check_wallet_key("admin")
async def api_link_delete(link_id):
    link = await get_withdraw_link(link_id)

    if not link:
        return (
            jsonify({"message": "Withdraw link does not exist."}),
            HTTPStatus.NOT_FOUND,
        )

    if link.wallet != g.wallet.id:
        return jsonify({"message": "Not your withdraw link."}), HTTPStatus.FORBIDDEN

    await delete_withdraw_link(link_id)

    return "", HTTPStatus.NO_CONTENT


@withdrawfiat_ext.route("/api/v1/links/<the_hash>/<lnurl_id>", methods=["GET"])
@api_check_wallet_key("invoice")
async def api_hash_retrieve(the_hash, lnurl_id):
    hashCheck = await get_hash_check(the_hash, lnurl_id)
    return jsonify(hashCheck), HTTPStatus.OK

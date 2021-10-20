from http import HTTPStatus
from lnbits.utils.exchange_rates import fiat_amount_as_satoshis
from quart import jsonify, request

from lnbits import bolt11
from lnbits.core.services import pay_invoice

from . import withdrawfiat_ext
from .crud import get_withdraw_link_by_hash, update_withdraw_link


# FOR LNURLs WHICH ARE NOT UNIQUE


@withdrawfiat_ext.route("/api/v1/lnurl/<unique_hash>", methods=["GET"])
async def api_lnurl_response(unique_hash):
    link = await get_withdraw_link_by_hash(unique_hash)

    if not link:
        return (
            jsonify({"status": "ERROR", "reason": "LNURL-withdraw not found."}),
            HTTPStatus.OK,
        )

    if link.is_spent:
        return (
            jsonify({"status": "ERROR", "reason": "Withdraw is spent."}),
            HTTPStatus.OK,
        )

    sats = await fiat_amount_as_satoshis(link.amount, link.currency)
    changes = {
        "max_satoshis": sats
    }
    await update_withdraw_link(link.id, **changes)
    return jsonify(link.lnurl_response(sats).dict()), HTTPStatus.OK


# CALLBACK


@withdrawfiat_ext.route("/api/v1/lnurl/cb/<unique_hash>", methods=["GET"])
async def api_lnurl_callback(unique_hash):
    link = await get_withdraw_link_by_hash(unique_hash)
    k1 = request.args.get("k1", type=str)
    payment_request = request.args.get("pr", type=str)

    if not link:
        return (
            jsonify({"status": "ERROR", "reason": "LNURL-withdraw not found."}),
            HTTPStatus.OK,
        )

    if link.is_spent:
        return (
            jsonify({"status": "ERROR", "reason": "Withdraw is spent."}),
            HTTPStatus.OK,
        )

    if link.k1 != k1:
        return jsonify({"status": "ERROR", "reason": "Bad request."}), HTTPStatus.OK


    try:
        invoice = bolt11.decode(payment_request)
        changesback = {
            "used": link.used,
            "settled_msats": None,
        }

        changes = {
            "used": 1,
            "settled_msats": invoice.amount_msat
        }

        await update_withdraw_link(link.id, **changes)

        await pay_invoice(
            wallet_id=link.wallet,
            payment_request=payment_request,
            max_sat=link.max_satoshis,
            extra={"tag": "withdraw"},
        )
    except ValueError as e:
        await update_withdraw_link(link.id, **changesback)
        return jsonify({"status": "ERROR", "reason": str(e)})
    except PermissionError:
        await update_withdraw_link(link.id, **changesback)
        return jsonify({"status": "ERROR", "reason": "Withdraw link is empty."})
    except Exception as e:
        await update_withdraw_link(link.id, **changesback)
        return jsonify({"status": "ERROR", "reason": str(e)})

    return jsonify({"status": "OK"}), HTTPStatus.OK

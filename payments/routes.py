from flask import jsonify, request

from payments import payments_bp
from payments import stripe_service


@payments_bp.route("/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    if not stripe_service.is_configured():
        return jsonify({"ok": False, "error": "Stripe not configured"}), 503

    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        result = stripe_service.handle_webhook_event(payload, sig)
    except stripe_service.PaymentError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, **result})

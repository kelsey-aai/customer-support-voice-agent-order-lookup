"""
Tools the customer support voice agent can call.

Replace the stub implementations in dispatch_tool with calls to your real
order management system, returns API, scheduling backend, and contact center.
"""

import json

TOOLS = [
    {
        "type": "function",
        "name": "get_order_status",
        "description": (
            "Look up the status of a customer order by ID. Returns shipping "
            "status and dates for shipped, processing, or delivered orders."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The caller's order ID, e.g. AB3792",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "type": "function",
        "name": "initiate_return",
        "description": (
            "Start a return for a delivered order. Emails a return label "
            "to the address on file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {
                    "type": "string",
                    "description": "Why the caller is returning the item.",
                },
            },
            "required": ["order_id", "reason"],
        },
    },
    {
        "type": "function",
        "name": "schedule_callback",
        "description": "Schedule a callback to the caller.",
        "parameters": {
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "Caller's phone number, any format.",
                },
                "preferred_time": {
                    "type": "string",
                    "description": "When the caller would like to be called.",
                },
            },
            "required": ["phone"],
        },
    },
    {
        "type": "function",
        "name": "transfer_to_human",
        "description": (
            "Transfer the caller to a human agent. Call this when the caller "
            "asks for a person, sounds upset, or wants something outside "
            "order status, returns, or callbacks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why we're transferring.",
                },
            },
            "required": ["reason"],
        },
    },
]


# Demo orders. Replace with a real OMS lookup in production.
_ORDERS = {
    "AB3792": {"status": "shipped", "eta": "Thursday, May 14"},
    "CD1204": {"status": "processing", "ships_in": "2 business days"},
    "EF5566": {"status": "delivered", "delivered_on": "May 8"},
    "GH8821": {"status": "delivered", "delivered_on": "April 30"},
}


async def dispatch_tool(name: str, arguments) -> str:
    args = arguments if isinstance(arguments, dict) else json.loads(arguments)

    if name == "get_order_status":
        order_id = args["order_id"].upper().replace(" ", "")
        order = _ORDERS.get(order_id)
        if not order:
            return f"No order found with ID {order_id}."
        status = order["status"]
        if status == "shipped":
            return f"Order {order_id} shipped. Expected {order['eta']}."
        if status == "processing":
            return f"Order {order_id} is processing. Ships in {order['ships_in']}."
        if status == "delivered":
            return f"Order {order_id} was delivered on {order['delivered_on']}."

    if name == "initiate_return":
        # In production: call your returns API and email a label.
        print(f"[RETURN] {args['order_id']} — reason: {args['reason']}")
        return (
            f"Return started for {args['order_id']}. "
            "Return label emailed to the address on file."
        )

    if name == "schedule_callback":
        # In production: write to your scheduling backend.
        when = args.get("preferred_time") or "within 2 hours"
        print(f"[CALLBACK] {args['phone']} at {when}")
        return f"Callback scheduled to {args['phone']} {when}."

    if name == "transfer_to_human":
        # In production: hand off to your contact center with full context.
        print(f"[TRANSFER] reason: {args['reason']}")
        return "Transferring you now. Please hold for just a moment."

    return f"Unknown tool: {name}"

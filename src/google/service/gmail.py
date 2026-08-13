import asyncer

from googleapiclient.discovery import Resource

from src.google.schemas import GmailInboxQuery, GmailMessageResponse
from src.google.service.parser import parse_gmail_message
from src.schemas import PaginationQuery


async def get_current_user_email(service: Resource) -> str | None:
    stmt = service.users().getProfile(userId="me")
    profile = await asyncer.asyncify(stmt.execute)()

    return profile.get("emailAddress")


async def get_gmail_messages(
    service: Resource,
    pagination: PaginationQuery,
    query: GmailInboxQuery,
) -> dict:
    gmail_query = query.to_gmail_query()
    fetch_size = pagination.offset + pagination.limit

    stmt = service.users().messages().list(
        userId="me",
        maxResults=fetch_size,
        q=gmail_query,
    )
    results = await asyncer.asyncify(stmt.execute)()
    message_refs = results.get("messages", [])[
        pagination.offset : pagination.offset + pagination.limit
    ]

    message_details = []
    for message in message_refs:
        message_details.append(await _get_gmail_message_detail(service, message))

    return {
        "messages": [
            GmailMessageResponse(**parse_gmail_message(message)).model_dump()
            for message in message_details
        ],
        "result_size_estimate": results.get("resultSizeEstimate"),
    }


async def _get_gmail_message_detail(service: Resource, message: dict) -> dict:
    stmt = service.users().messages().get(
        userId="me",
        id=message["id"],
        format="full",
    )

    return await asyncer.asyncify(stmt.execute)()

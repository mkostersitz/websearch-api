"""
Migration: promote metadata.role to top-level role field on client documents.

Run once against any existing deployment before deploying the new code.
Safe to run multiple times (idempotent).
"""

import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def migrate():
    mongo_url = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("MONGODB_DB_NAME", "websearch_api")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    clients = db.clients
    total = await clients.count_documents({})
    print(f"Found {total} client documents")

    promoted = 0
    defaulted = 0

    async for doc in clients.find({}):
        # Skip documents that already have a top-level role
        if doc.get("role"):
            continue

        metadata_role = doc.get("metadata", {}).get("role")
        new_role = metadata_role if metadata_role in ("admin", "user", "agent") else "agent"

        update = {"$set": {"role": new_role}}
        if metadata_role:
            # Remove role from metadata now that it lives at the top level
            update["$unset"] = {"metadata.role": ""}

        await clients.update_one({"client_id": doc["client_id"]}, update)

        if metadata_role:
            promoted += 1
            print(f"  Promoted {doc['client_id']}: metadata.role={metadata_role!r} -> role={new_role!r}")
        else:
            defaulted += 1

    print(f"\nDone: {promoted} promoted from metadata.role, {defaulted} defaulted to 'agent'")
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())

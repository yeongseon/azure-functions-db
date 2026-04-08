from azure_functions_db import PollTrigger, SqlAlchemySource, BlobCheckpointStore

trigger = PollTrigger(
    name="orders",
    source=SqlAlchemySource(
        url="postgresql+psycopg://postgres:postgres@localhost:5432/orders",
        table="orders",
        schema="public",
        cursor_column="updated_at",
        pk_columns=["id"],
    ),
    checkpoint_store=BlobCheckpointStore(
        connection="AzureWebJobsStorage",
        container="db-state",
    ),
)

def handler(events, context):
    for event in events:
        print(event.event_id, event.pk, event.after)

# pseudo code
# trigger.run(timer=fake_timer_request, handler=handler)

import azure.functions as func

from azure_functions_db import PollTrigger, SqlAlchemySource, BlobCheckpointStore

app = func.FunctionApp()

orders_trigger = PollTrigger(
    name="orders",
    source=SqlAlchemySource(
        url="%ORDERS_DB_URL%",
        table="orders",
        schema="public",
        cursor_column="updated_at",
        pk_columns=["id"],
    ),
    checkpoint_store=BlobCheckpointStore(
        connection="AzureWebJobsStorage",
        container="db-state",
    ),
    batch_size=100,
    max_batches_per_tick=1,
)

def handle_orders(events, context) -> None:
    for event in events:
        print(
            {
                "event_id": event.event_id,
                "op": event.op,
                "pk": event.pk,
                "after": event.after,
            }
        )

@app.function_name(name="orders_poll")
@app.schedule(schedule="0 */1 * * * *", arg_name="timer", use_monitor=True)
def orders_poll(timer: func.TimerRequest) -> None:
    orders_trigger.run(timer=timer, handler=handle_orders)

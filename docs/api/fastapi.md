# FastAPI Example

The example app demonstrates how to reject incoming data at the API boundary.

```bash
uvicorn examples.fastapi_app:app --reload
```

Requests that fail the declared policy receive an HTTP 422 response.

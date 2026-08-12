from __future__ import annotations

from stocks.integrations.contracts import IntegrationState, WorkerRequest, WorkerResponse


def test_worker_contract_roundtrip() -> None:
    request = WorkerRequest(integration="qlib", action="health", payload={"x": 1})
    restored = WorkerRequest.from_dict(request.to_dict())
    assert restored == request

    response = WorkerResponse(
        integration="qlib",
        action="health",
        request_id=request.request_id,
        state=IntegrationState.OK,
        data={"version": "x"},
    )
    restored_response = WorkerResponse.from_dict(response.to_dict())
    assert restored_response == response
    assert restored_response.ok

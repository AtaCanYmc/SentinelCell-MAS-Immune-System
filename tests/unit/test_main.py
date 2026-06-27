from unittest.mock import patch


@patch("src.main.uvicorn.run")
def test_main(mock_run):
    from src.main import main

    main()
    mock_run.assert_called_once_with(
        "src.gateways.fastapi_gateway:app", host="0.0.0.0", port=8000, reload=False
    )

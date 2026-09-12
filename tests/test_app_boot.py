from asset_management.app import create_app


def test_application_boots() -> None:
    app = create_app()

    assert app.title == "Asset Management"

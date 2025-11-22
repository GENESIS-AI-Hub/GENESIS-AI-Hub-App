#conftest.py
import os
import sys
import importlib
import pytest
from fastapi.testclient import TestClient

THIS_DIR = os.path.dirname(__file__)
BACK_DIR = os.path.abspath(os.path.join(THIS_DIR, ".."))
if BACK_DIR not in sys.path:
    sys.path.insert(0, BACK_DIR)

@pytest.fixture
def app_and_state():
    if "main" in sys.modules:
        importlib.reload(sys.modules["main"])
        main = sys.modules["main"]
    else:
        main = importlib.import_module("main")

    app = main.app

    main.chats_db.clear()
    main.messages_db.clear()
    main.agents_db.clear()

    for handler in app.router.on_startup:
        handler()

    return app, main

@pytest.fixture
def client(app_and_state):
    app, _ = app_and_state
    with TestClient(app) as c:
        yield c

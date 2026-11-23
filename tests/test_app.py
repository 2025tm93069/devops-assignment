import sqlite3
from unittest.mock import Mock

import app as app_module
import pytest
from app import ACEestApp


@pytest.fixture
def app():
    application = ACEestApp.__new__(ACEestApp)
    application.conn = sqlite3.connect(":memory:")
    application.cur = application.conn.cursor()
    application.cur.execute(
        """
        CREATE TABLE clients (
            name TEXT PRIMARY KEY,
            program TEXT,
            membership_status TEXT,
            membership_end TEXT
        )
        """
    )
    application.cur.execute(
        "INSERT INTO clients VALUES (?, ?, ?, ?)",
        ("Test Client", None, "Active", "2026-12-01"),
    )
    application.conn.commit()

    application.current_client = "Test Client"
    application.program_templates = {"Fat Loss": ["Full Body HIIT"]}
    application.refresh_summary = Mock()

    yield application

    application.conn.close()


def test_generate_program_updates_selected_client(app, monkeypatch):
    monkeypatch.setattr(app_module.random, "choice", lambda options: options[0])
    showinfo = Mock()
    monkeypatch.setattr(app_module.messagebox, "showinfo", showinfo)

    app.generate_program()

    app.cur.execute("SELECT program FROM clients WHERE name=?", ("Test Client",))
    assert app.cur.fetchone() == ("Full Body HIIT",)
    app.refresh_summary.assert_called_once_with()
    showinfo.assert_called_once_with(
        "Program Generated", "Program for Test Client: Full Body HIIT"
    )


def test_generate_program_requires_selected_client(app, monkeypatch):
    app.current_client = None
    showwarning = Mock()
    monkeypatch.setattr(app_module.messagebox, "showwarning", showwarning)

    app.generate_program()

    showwarning.assert_called_once_with("No Client", "Select a client first")
    app.refresh_summary.assert_not_called()


def test_check_membership_displays_status(app, monkeypatch):
    showinfo = Mock()
    monkeypatch.setattr(app_module.messagebox, "showinfo", showinfo)

    app.check_membership()

    showinfo.assert_called_once_with(
        "Membership", "Membership: Active\nRenewal Date: 2026-12-01"
    )

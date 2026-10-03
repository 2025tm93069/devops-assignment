import pytest

from app import ACEestApp


class MockVariable:
    """Mock replacement for tkinter.StringVar."""

    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class MockLabel:
    """Mock replacement for tkinter.Label."""

    def __init__(self):
        self.config_values = {}

    def config(self, **kwargs):
        self.config_values.update(kwargs)


@pytest.fixture
def app():
    """
    Create ACEestApp without launching the Tkinter GUI.

    This allows the internal program data and update_display()
    logic to be tested in a headless CI/CD environment.
    """
    application = ACEestApp.__new__(ACEestApp)

    application.programs = {
        "Fat Loss (FL)": {
            "workout": (
                "Mon: 5x5 Back Squat + AMRAP\n"
                "Tue: EMOM 20min Assault Bike\n"
                "Wed: Bench Press + 21-15-9\n"
                "Thu: 10RFT Deadlifts/Box Jumps\n"
                "Fri: 30min Active Recovery"
            ),
            "diet": (
                "B: 3 Egg Whites + Oats Idli\n"
                "L: Grilled Chicken + Brown Rice\n"
                "D: Fish Curry + Millet Roti\n"
                "Target: 2,000 kcal"
            ),
            "color": "#e74c3c",
        },
        "Muscle Gain (MG)": {
            "workout": (
                "Mon: Squat 5x5\n"
                "Tue: Bench 5x5\n"
                "Wed: Deadlift 4x6\n"
                "Thu: Front Squat 4x8\n"
                "Fri: Incline Press 4x10\n"
                "Sat: Barbell Rows 4x10"
            ),
            "diet": (
                "B: 4 Eggs + PB Oats\n"
                "L: Chicken Biryani (250g Chicken)\n"
                "D: Mutton Curry + Jeera Rice\n"
                "Target: 3,200 kcal"
            ),
            "color": "#2ecc71",
        },
        "Beginner (BG)": {
            "workout": (
                "Circuit Training: Air Squats, Ring Rows, Push-ups.\n"
                "Focus: Technique Mastery & Form (90% Threshold)"
            ),
            "diet": (
                "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\n"
                "Protein: 120g/day"
            ),
            "color": "#3498db",
        },
    }

    application.prog_var = MockVariable()
    application.work_label = MockLabel()
    application.diet_label = MockLabel()

    return application


def test_program_count(app):
    """Application should contain exactly three fitness programs."""
    assert len(app.programs) == 3


def test_program_names(app):
    """All required fitness programs should be available."""
    assert set(app.programs.keys()) == {
        "Fat Loss (FL)",
        "Muscle Gain (MG)",
        "Beginner (BG)",
    }


@pytest.mark.parametrize(
    "program",
    [
        "Fat Loss (FL)",
        "Muscle Gain (MG)",
        "Beginner (BG)",
    ],
)
def test_program_has_required_fields(app, program):
    """Every program should contain workout, diet and color information."""
    data = app.programs[program]

    assert "workout" in data
    assert "diet" in data
    assert "color" in data

    assert data["workout"]
    assert data["diet"]
    assert data["color"]


def test_fat_loss_workout(app):
    """Fat Loss program should contain its specified workout plan."""
    workout = app.programs["Fat Loss (FL)"]["workout"]

    assert "Back Squat" in workout
    assert "Assault Bike" in workout
    assert "Bench Press" in workout
    assert "Deadlifts/Box Jumps" in workout
    assert "Active Recovery" in workout


def test_fat_loss_diet(app):
    """Fat Loss program should contain its specified nutrition plan."""
    diet = app.programs["Fat Loss (FL)"]["diet"]

    assert "Egg Whites" in diet
    assert "Brown Rice" in diet
    assert "Fish Curry" in diet
    assert "2,000 kcal" in diet


def test_muscle_gain_workout(app):
    """Muscle Gain program should contain its specified workout plan."""
    workout = app.programs["Muscle Gain (MG)"]["workout"]

    assert "Squat 5x5" in workout
    assert "Bench 5x5" in workout
    assert "Deadlift 4x6" in workout
    assert "Barbell Rows 4x10" in workout


def test_muscle_gain_diet(app):
    """Muscle Gain program should contain its specified nutrition plan."""
    diet = app.programs["Muscle Gain (MG)"]["diet"]

    assert "4 Eggs" in diet
    assert "Chicken Biryani" in diet
    assert "Mutton Curry" in diet
    assert "3,200 kcal" in diet


def test_beginner_program(app):
    """Beginner program should contain the expected workout and diet."""
    data = app.programs["Beginner (BG)"]

    assert "Air Squats" in data["workout"]
    assert "Ring Rows" in data["workout"]
    assert "Push-ups" in data["workout"]
    assert "Idli-Sambar" in data["diet"]
    assert "120g/day" in data["diet"]


@pytest.mark.parametrize(
    "program, expected_color",
    [
        ("Fat Loss (FL)", "#e74c3c"),
        ("Muscle Gain (MG)", "#2ecc71"),
        ("Beginner (BG)", "#3498db"),
    ],
)
def test_program_colors(app, program, expected_color):
    """Each program should use its specified display color."""
    assert app.programs[program]["color"] == expected_color


def test_update_display_fat_loss(app):
    """Selecting Fat Loss should update workout and diet displays."""
    app.prog_var.set("Fat Loss (FL)")

    app.update_display(None)

    assert (
        app.work_label.config_values["text"]
        == app.programs["Fat Loss (FL)"]["workout"]
    )

    assert (
        app.work_label.config_values["fg"]
        == app.programs["Fat Loss (FL)"]["color"]
    )

    assert (
        app.diet_label.config_values["text"]
        == app.programs["Fat Loss (FL)"]["diet"]
    )


def test_update_display_muscle_gain(app):
    """Selecting Muscle Gain should update the displayed information."""
    app.prog_var.set("Muscle Gain (MG)")

    app.update_display(None)

    assert (
        app.work_label.config_values["text"]
        == app.programs["Muscle Gain (MG)"]["workout"]
    )

    assert (
        app.diet_label.config_values["text"]
        == app.programs["Muscle Gain (MG)"]["diet"]
    )


def test_update_display_beginner(app):
    """Selecting Beginner should update the displayed information."""
    app.prog_var.set("Beginner (BG)")

    app.update_display(None)

    assert (
        app.work_label.config_values["text"]
        == app.programs["Beginner (BG)"]["workout"]
    )

    assert (
        app.diet_label.config_values["text"]
        == app.programs["Beginner (BG)"]["diet"]
    )
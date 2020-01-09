from api import APIReader


def test_answer():
    api = APIReader()
    api.update()

    assert len(api.active_mission_details) > 1
    for mission in api.active_mission_details:
        assert len(mission) == 4


if __name__ == "__main__":
    test_answer()

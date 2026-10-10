"""#73: the student module counts down a timed question's time_limit_s and
stops taking presses once it is up (the backend refuses late answers too)."""

from c_source import FIRMWARE, calls, functions, mentions

MAIN = FIRMWARE / "student" / "main" / "main.c"


def test_question_frame_sets_the_deadline_from_time_limit():
    body = functions(MAIN)["on_mesh_message"]
    assert "time_limit_s" in body and mentions(body, "s_deadline") and mentions(body, "s_timed")


def test_presses_after_the_deadline_send_nothing():
    body = functions(MAIN)["on_button_press"]
    quiz = body[body.index("STATE_QUIZ_ACTIVE"):body.index("STATE_POLL_ACTIVE")]
    assert quiz.index("time_is_up") < quiz.index("mesh_send")


def test_main_loop_shows_the_countdown_and_closes_the_question():
    body = functions(MAIN)["app_main"]
    loop = body[body.rindex("while (1)"):]
    assert calls(loop, "display_show_countdown") and calls(loop, "time_is_up")
    assert "STATE_IDLE" in loop


def test_deadline_comparison_survives_tick_wrap():
    assert "(int32_t)(s_deadline - xTaskGetTickCount())" in functions(MAIN)["ticks_left"]

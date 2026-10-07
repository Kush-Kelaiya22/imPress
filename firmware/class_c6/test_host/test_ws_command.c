/* Host test for main/ws_command.c (#3): backend WS JSON → mesh frame.
 *
 * Feeds the frames the backend really sends (firmware/contract/
 * device_ws_frames.json, pinned by backend/tests/test_device_ws_contract.py)
 * through ws_command_to_frame(), decodes the result and reads it back with
 * the same packed structs the student firmware casts to.
 * Run: ./run_ws_command.sh
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ws_command.h"

#define CHECK(c) do { if (!(c)) { printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); exit(1); } } while (0)

static msg_t frame_of(const char *json, int expect_len_sign)
{
    cJSON *j = cJSON_Parse(json);
    CHECK(j);
    uint8_t out[MSG_MAX_SIZE];
    int n = ws_command_to_frame(j, out, sizeof out);
    cJSON_Delete(j);
    msg_t m = {0};
    if (expect_len_sign > 0) {
        CHECK(n > 0);
        CHECK(msg_decode(out, n, &m) == n && msg_verify_crc(&m));
    } else {
        CHECK(n == expect_len_sign);
    }
    return m;
}

static char *read_file(const char *path)
{
    FILE *f = fopen(path, "rb");
    CHECK(f);
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    char *buf = calloc(1, sz + 1);
    CHECK(fread(buf, 1, sz, f) == (size_t)sz);
    fclose(f);
    return buf;
}

static void test_backend_contract_fixture(void)
{
    char *txt = read_file("../../contract/device_ws_frames.json");
    cJSON *arr = cJSON_Parse(txt);
    CHECK(cJSON_IsArray(arr) && cJSON_GetArraySize(arr) == 5);
    const msg_type_t want[5] = { MSG_QUIZ_QUESTION, MSG_QUIZ_QUESTION, MSG_QUIZ_END,
                                 MSG_POLL_START, MSG_POLL_END };
    for (int i = 0; i < 5; i++) {
        char *one = cJSON_PrintUnformatted(cJSON_GetArrayItem(arr, i));
        msg_t m = frame_of(one, 1);
        CHECK(m.type == want[i]);
        free(one);
        if (i == 0) {
            const payload_quiz_question_t *q = (const void *)m.payload;
            CHECK(m.length == sizeof *q);
            CHECK(q->quiz_id == 1 && q->question_num == 0 && q->num_options == 4);
            CHECK(q->time_limit_s == 30);
            CHECK(strcmp(q->question_text, "2+2?") == 0 && strcmp(q->options[1], "4") == 0);
        } else if (i == 1) {
            const payload_quiz_question_t *q = (const void *)m.payload;
            CHECK(q->question_num == 1 && q->num_options == 2);
            CHECK(strcmp(q->options[0], "Paris") == 0);
        } else if (i == 3) {
            /* Exactly what student/main/main.c reads for MSG_POLL_START. */
            const payload_poll_start_t *p = (const void *)m.payload;
            CHECK(m.length == sizeof *p);
            CHECK(p->poll_id == 1 && p->num_options == 3);
            CHECK(strcmp(p->title, "Lab on Friday?") == 0);
        } else {
            const payload_session_end_t *e = (const void *)m.payload;
            CHECK(m.length == sizeof *e && e->id == 1);
        }
    }
    cJSON_Delete(arr);
    free(txt);
    puts("ok   test_backend_contract_fixture");
}

static void test_edges(void)
{
    /* Not a mesh command → 0 (main.c falls through to device_command etc.). */
    frame_of("{\"event\":\"connected\",\"class_id\":3}", 0);
    frame_of("{\"type\":\"quiz_question\",\"quiz_id\":1}", 0);   /* legacy key only */
    /* Mesh command missing required fields → -1, nothing sent. */
    frame_of("{\"event\":\"quiz_question\",\"quiz_id\":1}", -1);
    frame_of("{\"event\":\"poll_start\",\"options\":[\"a\"]}", -1);
    frame_of("{\"event\":\"quiz_end\"}", -1);

    /* 6 options (backend max) clamp to the 4 buttons; long text truncated + NUL. */
    char json[1024], longq[400];
    memset(longq, 'x', sizeof longq - 1);
    longq[sizeof longq - 1] = '\0';
    snprintf(json, sizeof json,
             "{\"event\":\"quiz_question\",\"quiz_id\":7,\"question_num\":3,\"time_limit\":9,"
             "\"question_text\":\"%s\",\"options\":[\"aaaaaaaaaaaaaaaaaaaaaaa\",\"b\",\"c\",\"d\",\"e\",\"f\"]}",
             longq);
    msg_t m = frame_of(json, 1);
    const payload_quiz_question_t *q = (const void *)m.payload;
    CHECK(q->num_options == 4);
    CHECK(q->question_num == 3 && q->time_limit_s == 9);           /* legacy key fallbacks */
    CHECK(strlen(q->question_text) == sizeof q->question_text - 1);
    CHECK(strlen(q->options[0]) == sizeof q->options[0] - 1);
    puts("ok   test_edges");
}

int main(void)
{
    test_backend_contract_fixture();
    test_edges();
    puts("PASS test_ws_command");
    return 0;
}

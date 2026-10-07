/**
 * @file ws_command.c
 * @brief Backend WebSocket command (JSON) → mesh protocol frame.
 */

#include "ws_command.h"

#include <string.h>

#define MAX_BUTTON_OPTIONS 4   /* student modules have buttons A-D */

static const cJSON *num_item(const cJSON *o, const char *key)
{
    const cJSON *v = cJSON_GetObjectItem(o, key);
    return cJSON_IsNumber(v) ? v : NULL;
}

static int num_or(const cJSON *o, const char *key, int dflt)
{
    const cJSON *v = num_item(o, key);
    return v ? v->valueint : dflt;
}

static const char *str_or_null(const cJSON *o, const char *key)
{
    const cJSON *v = cJSON_GetObjectItem(o, key);
    return cJSON_IsString(v) ? v->valuestring : NULL;
}

static uint8_t clamp_options(const cJSON *options)
{
    int n = cJSON_GetArraySize(options);
    return (uint8_t)(n > MAX_BUTTON_OPTIONS ? MAX_BUTTON_OPTIONS : n);
}

int ws_command_to_frame(const cJSON *msg, uint8_t *out, size_t out_size)
{
    const char *evt = str_or_null(msg, "event");
    if (!evt) {
        return 0;
    }

    if (strcmp(evt, "quiz_question") == 0) {
        const char *text = str_or_null(msg, "question_text");
        const cJSON *options = cJSON_GetObjectItem(msg, "options");
        if (!num_item(msg, "quiz_id") || !text || !cJSON_IsArray(options)) {
            return -1;
        }
        payload_quiz_question_t q = {0};
        q.quiz_id = (uint16_t)num_or(msg, "quiz_id", 0);
        q.question_num = (uint8_t)num_or(msg, "question_order", num_or(msg, "question_num", 0));
        q.num_options = clamp_options(options);
        q.time_limit_s = (uint32_t)num_or(msg, "time_limit_s", num_or(msg, "time_limit", 0));
        strncpy(q.question_text, text, sizeof(q.question_text) - 1);
        for (int i = 0; i < q.num_options; i++) {
            const cJSON *opt = cJSON_GetArrayItem(options, i);
            if (cJSON_IsString(opt)) {
                strncpy(q.options[i], opt->valuestring, sizeof(q.options[i]) - 1);
            }
        }
        return msg_encode(MSG_QUIZ_QUESTION, (const uint8_t *)&q, sizeof(q), out, out_size);
    }

    if (strcmp(evt, "poll_start") == 0) {
        const cJSON *options = cJSON_GetObjectItem(msg, "options");
        if (!num_item(msg, "poll_id") || !cJSON_IsArray(options)) {
            return -1;
        }
        payload_poll_start_t p = {0};
        p.poll_id = (uint16_t)num_or(msg, "poll_id", 0);
        p.num_options = clamp_options(options);
        const char *title = str_or_null(msg, "title");
        if (title) {
            strncpy(p.title, title, sizeof(p.title) - 1);
        }
        return msg_encode(MSG_POLL_START, (const uint8_t *)&p, sizeof(p), out, out_size);
    }

    if (strcmp(evt, "quiz_end") == 0 || strcmp(evt, "poll_end") == 0) {
        bool quiz = evt[0] == 'q';
        const char *key = quiz ? "quiz_id" : "poll_id";
        if (!num_item(msg, key)) {
            return -1;
        }
        payload_session_end_t e = { .id = (uint16_t)num_or(msg, key, 0) };
        return msg_encode(quiz ? MSG_QUIZ_END : MSG_POLL_END, (const uint8_t *)&e,
                          sizeof(e), out, out_size);
    }

    return 0;
}

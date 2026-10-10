/**
 * @file display.h
 * @brief OLED display driver for student module.
 */

#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int display_init(void);
void display_clear(void);
void display_show_text(const char *line1, const char *line2, const char *line3);
void display_show_status(const char *status, int battery_pct);
void display_show_question(const char *question, const char *options[], int num_options, int selected);
void display_show_result(const char *text);
void display_show_countdown(int seconds_left);
void display_show_waiting(const char *message);
void display_show_provision_state(const char *title, const char *id,
                                  int cursor, const char *hint);
void display_deinit(void);

#ifdef __cplusplus
}
#endif

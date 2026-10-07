/**
 * @file input.h
 * @brief Button input handling for student module.
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*input_cb_t)(int button);  /* button = 0-3 for A-D, 4 for confirm */

int input_init(input_cb_t callback);
bool input_is_button_pressed(int button);
int input_get_last_button(void);

#ifdef __cplusplus
}
#endif

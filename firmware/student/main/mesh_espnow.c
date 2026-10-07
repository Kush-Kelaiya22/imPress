/**
 * @file mesh_espnow.c
 * @brief ESP-NOW mesh implementation for student module.
 *
 * Architecture:
 *  - Students use ESP-NOW broadcast to reach S3 root node
 *  - If a student can't reach S3 directly, other students relay the message
 *  - S3 root sends commands via broadcast → all students receive
 *  - Each message has a TTL to prevent infinite relay loops
 */

#include "mesh_espnow.h"
#include "config.h"

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_now.h"
#include "esp_random.h"
#include "nvs_flash.h"

static const char *TAG = "mesh_student";

/* Broadcast destination — ESP-NOW requires the peer entry to be present in
 * the peer list at send time; NULL ("all peers") path misreports NOT_FOUND
 * in this IDF fork, so send explicitly to the broadcast MAC. */
static const uint8_t s_broadcast_mac[6] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

/* ── Internal State ────────────────────────────────────────────────── */

#define IS_ROOT_FLAG     (1 << 0)
#define IS_CONNECTED     (1 << 1)

static EventGroupHandle_t s_mesh_event_group;
static uint32_t s_device_id;
static uint16_t s_student_id;
static mesh_recv_cb_t s_recv_callback;

/* Relay tracking: avoid relaying same message twice */
#define RELAY_CACHE_SIZE 64
static struct {
    uint32_t msg_hash;
    uint32_t timestamp;
} s_relay_cache[RELAY_CACHE_SIZE];
static int s_relay_cache_idx;

/* Root node MAC (S3) — learned from received messages */
static uint8_t s_root_mac[6];
static bool s_root_known = false;
static int s_hop_count = 99;

/* ── Helpers ───────────────────────────────────────────────────────── */

static uint32_t compute_msg_hash(const uint8_t *data, size_t len)
{
    /* Simple FNV-1a hash for relay dedup */
    uint32_t hash = 2166136261u;
    for (size_t i = 0; i < len && i < 20; i++) {  /* hash first 20 bytes */
        hash ^= data[i];
        hash *= 16777619u;
    }
    return hash;
}

static bool should_relay(const uint8_t *raw_msg, size_t raw_len)
{
    uint32_t hash = compute_msg_hash(raw_msg, raw_len);
    uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;

    for (int i = 0; i < RELAY_CACHE_SIZE; i++) {
        if (s_relay_cache[i].msg_hash == hash) {
            return false;  /* already relayed */
        }
    }

    /* Add to cache */
    s_relay_cache[s_relay_cache_idx].msg_hash = hash;
    s_relay_cache[s_relay_cache_idx].timestamp = now;
    s_relay_cache_idx = (s_relay_cache_idx + 1) % RELAY_CACHE_SIZE;
    return true;
}

/**
 * @brief Custom framing for mesh transport: adds TTL + sender info
 *        before the standard protocol message.
 *
 *   [TTL:1][SENDER_ID:4][HOPS:1][MSG_BYTES...]
 *   This is prepended to the raw protocol bytes.
 */
typedef struct __attribute__((packed)) {
    uint8_t  ttl;
    uint32_t sender_id;
    uint8_t  hops;
} mesh_header_t;

#define MESH_HEADER_SIZE sizeof(mesh_header_t)

/* ── ESP-NOW Receive Callback ──────────────────────────────────────── */

static void on_espnow_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len)
{
    if (!info || !data || len < (int)MESH_HEADER_SIZE) {
        return;
    }

    const mesh_header_t *hdr = (const mesh_header_t *)data;

    /* Don't process our own messages */
    if (hdr->sender_id == s_device_id) {
        return;
    }

    /* Learn root MAC from messages with TTL = max (originated by root) */
    if (hdr->ttl == MESH_RELAY_TTL && !s_root_known) {
        memcpy(s_root_mac, info->src_addr, 6);
        s_root_known = true;
        s_hop_count = hdr->hops + 1;
        xEventGroupSetBits(s_mesh_event_group, IS_CONNECTED);
        ESP_LOGI(TAG, "Root node found, hop count: %d", s_hop_count);
    }

    /* Check if message is addressed to us (broadcast from root) or relayable */
    bool for_us = (hdr->ttl == MESH_RELAY_TTL);  /* messages from root are for everyone */

    /* Parse the inner protocol message */
    const uint8_t *msg_data = data + MESH_HEADER_SIZE;
    int msg_len = len - MESH_HEADER_SIZE;

    if (for_us && s_recv_callback) {
        msg_t msg;
        int consumed = msg_decode(msg_data, msg_len, &msg);
        if (consumed > 0 && msg_verify_crc(&msg)) {
            s_recv_callback(&msg);
        }
    }

    /* Relay if TTL allows */
    if (hdr->ttl > 1 && should_relay(data, len)) {
        mesh_header_t relay_hdr = *hdr;
        relay_hdr.ttl--;
        relay_hdr.hops++;

        uint8_t relay_buf[MESH_HEADER_SIZE + MSG_MAX_SIZE];
        memcpy(relay_buf, &relay_hdr, MESH_HEADER_SIZE);
        memcpy(relay_buf + MESH_HEADER_SIZE, msg_data, msg_len);

        /* Small random delay to avoid collision with other relays */
        vTaskDelay(pdMS_TO_TICKS(10 + (esp_random() % 50)));

        esp_now_send(NULL /* broadcast */, relay_buf, MESH_HEADER_SIZE + msg_len);
    }
}

/* ── Public API ────────────────────────────────────────────────────── */

int mesh_init(uint32_t device_id)
{
    s_device_id = device_id;
    s_mesh_event_group = xEventGroupCreate();

    /* Initialize NVS (required by WiFi) */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ESP_ERROR_CHECK(nvs_flash_init());
    }

    /* Initialize WiFi in STA mode (no connection needed for ESP-NOW) */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    /* esp_wifi_set_channel() requires WiFi to be started first */
    ESP_ERROR_CHECK(esp_wifi_start());
    vTaskDelay(pdMS_TO_TICKS(100));  /* let WiFi radio settle */
    ret = esp_wifi_set_channel(MESH_WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_wifi_set_channel(%d) failed: %s",
                 MESH_WIFI_CHANNEL, esp_err_to_name(ret));
    }

    /* Initialize ESP-NOW */
    ESP_ERROR_CHECK(esp_now_init());
    ESP_ERROR_CHECK(esp_now_register_recv_cb(on_espnow_recv));

    /* Add broadcast peer */
    esp_now_peer_info_t broadcast_peer = {
        .channel = MESH_WIFI_CHANNEL,
        .ifidx = WIFI_IF_STA,
    };
    memset(broadcast_peer.peer_addr, 0xFF, 6);  /* broadcast */
    ret = esp_now_add_peer(&broadcast_peer);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_now_add_peer failed: %d (0x%X)", ret, ret);
    } else {
        ESP_LOGI(TAG, "Broadcast peer added successfully");
        vTaskDelay(pdMS_TO_TICKS(200));  /* let radio/peer table settle before first send */
    }

    ESP_LOGI(TAG, "Mesh initialized, device_id: %lu", (unsigned long)device_id);
    return 0;
}

int mesh_send(msg_type_t type, const uint8_t *payload, uint16_t length)
{
    /* Encode the protocol message */
    uint8_t msg_buf[MSG_MAX_SIZE];
    int msg_len = msg_encode(type, payload, length, msg_buf, sizeof(msg_buf));
    if (msg_len < 0) {
        ESP_LOGE(TAG, "Failed to encode message");
        return -1;
    }

    /* Prepend mesh header */
    mesh_header_t hdr = {
        .ttl = MESH_RELAY_TTL,
        .sender_id = s_device_id,
        .hops = 0,
    };

    uint8_t send_buf[MESH_HEADER_SIZE + MSG_MAX_SIZE];
    memcpy(send_buf, &hdr, MESH_HEADER_SIZE);
    memcpy(send_buf + MESH_HEADER_SIZE, msg_buf, msg_len);

    /* Rely on the explicitly-added broadcast peer; NULL dest reports
     * ESP_ERR_ESPNOW_NOT_FOUND in this IDF fork even when the peer exists. */
    esp_err_t ret = esp_now_send(s_broadcast_mac, send_buf,
                                 MESH_HEADER_SIZE + msg_len);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "esp_now_send (peer_exist=%d) failed: %d",
                 (int)esp_now_is_peer_exist(s_broadcast_mac), ret);
        return -1;
    }

    return 0;
}

void mesh_on_receive(mesh_recv_cb_t callback)
{
    s_recv_callback = callback;
}

bool mesh_is_connected(void)
{
    return (xEventGroupGetBits(s_mesh_event_group) & IS_CONNECTED) != 0;
}

int mesh_get_hop_count(void)
{
    return s_hop_count;
}

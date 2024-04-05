import time
import random
from collections import defaultdict

from flask import Flask, request, jsonify, abort

app = Flask(__name__)


def timestamp_ms():
    return int(time.time() * 1000)


class RateLimiter:
    def __init__(self, per_second_rate):
        self.__per_second_rate = per_second_rate
        self.__access_times = [0] * per_second_rate
        self.__curr_idx = 0

    def acquire_slot_if_possible(self):
        now = timestamp_ms()
        if now - self.__access_times[self.__curr_idx] > 1000:
            self.__access_times[self.__curr_idx] = now
            self.__curr_idx = (self.__curr_idx + 1) % self.__per_second_rate
            return True
        return False


class PerApiKeyState:
    def __init__(self):
        self.prev_nonce = 0
        self.rate_limiter = RateLimiter(20)
        self.error_429s = 0


VALID_API_KEYS = ['UT4NHL1J796WCHULA1750MXYF9F5JYA6',
                  '8TY2F3KIL38T741G1UCBMCAQ75XU9F5O',
                  '954IXKJN28CBDKHSKHURQIVLQHZIEEM9',
                  'EUU46ID478HOO7GOXFASKPOZ9P91XGYS',
                  '46V5EZ5K2DFAGW85J18L50SGO25WJ5JE']
per_api_key_state = defaultdict(lambda: PerApiKeyState())
MAX_LATENCY_MS = 50
MAX_429_REJECTS = 10


@app.route("/api/request", methods=["GET"])
def api_request():
    api_key = request.values.get('api_key')
    if api_key not in VALID_API_KEYS:
        return abort(401)

    state = per_api_key_state[api_key]
    incoming_latency_ms = random.randint(0, MAX_LATENCY_MS)
    time.sleep(incoming_latency_ms / 1000.0)

    if state.error_429s >= MAX_429_REJECTS:
        return abort(403)

    if not state.rate_limiter.acquire_slot_if_possible():
        state.error_429s += 1
        return abort(429)

    nonce = request.values.get('nonce')
    req_id = request.values.get('req_id')
    try:
        nonce = int(nonce)
        if nonce <= state.prev_nonce:
            return abort(400)
        state.prev_nonce = nonce
    except:
        return abort(400)

    outgoing_latency_ms = random.randint(0, MAX_LATENCY_MS)
    time.sleep(outgoing_latency_ms / 1000.0)

    return jsonify({"status": "OK", 'req_id': req_id})


@app.errorhandler(400)
def bad_nonce(e):
    outgoing_latency_ms = random.randint(0, MAX_LATENCY_MS)
    time.sleep(outgoing_latency_ms / 1000.0)
    return jsonify({"status": "error", "error_msg": "invalid nonce"}), 400


@app.errorhandler(401)
def bad_api_key(e):
    outgoing_latency_ms = random.randint(0, MAX_LATENCY_MS)
    time.sleep(outgoing_latency_ms / 1000.0)
    return jsonify({"status": "error", "error_msg": "invalid api key"}), 401


@app.errorhandler(429)
def too_many_requests(e):
    outgoing_latency_ms = random.randint(0, MAX_LATENCY_MS)
    time.sleep(outgoing_latency_ms / 1000.0)
    return jsonify({"status": "error", "error_msg": "exceeded rate limit"}), 429


@app.errorhandler(403)
def api_blocked(e):
    outgoing_latency_ms = random.randint(0, MAX_LATENCY_MS)
    time.sleep(outgoing_latency_ms / 1000.0)
    return jsonify({"status": "error", "error_msg": "too many rate limit errors: blocked"}), 429


app.run(port=9999)


import json
import os
import sys
import time
import random
import logging
import logging.handlers
import contextlib

import asyncio
from asyncio import Queue
import aiohttp
import async_timeout

# region: DO NOT CHANGE - the code within this region can be assumed to be "correct"

PER_SEC_RATE = 20
DURATION_MS_BETWEEN_REQUESTS = int(1000 / PER_SEC_RATE)
REQUEST_TTL_MS = 1000
VALID_API_KEYS = ['UT4NHL1J796WCHULA1750MXYF9F5JYA6',
                  '8TY2F3KIL38T741G1UCBMCAQ75XU9F5O',
                  '954IXKJN28CBDKHSKHURQIVLQHZIEEM9',
                  'EUU46ID478HOO7GOXFASKPOZ9P91XGYS',
                  '46V5EZ5K2DFAGW85J18L50SGO25WJ5JE']


async def generate_requests(queue: Queue):
    """
    co-routine responsible for generating requests

    :param queue:
    :param logger:
    :return:
    """
    curr_req_id = 0
    MAX_SLEEP_MS = int(1000 / PER_SEC_RATE / len(VALID_API_KEYS) * 1.05 * 2.0)
    while True:
        queue.put_nowait(Request(curr_req_id))
        curr_req_id += 1
        sleep_ms = random.randint(0, MAX_SLEEP_MS)
        await asyncio.sleep(sleep_ms / 1000.0)


def timestamp_ms() -> int:
    return int(time.time() * 1000)


# endregion


def configure_logger(name=None):
    logger = logging.getLogger(name)
    if name is None:
        log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
        logger.setLevel(log_level)
        # only add handlers to root logger
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if log_level == 'DEBUG':
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(formatter)
            logger.addHandler(sh)

        fh = logging.handlers.TimedRotatingFileHandler(
            'myapp_logs/async.log', when='H', interval=1, backupCount=720, encoding='utf-8'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


class RateLimiterTimeout(Exception):
    pass


class RateLimiter:
    def __init__(self, per_second_rate, min_duration_ms_between_requests):
        self.__per_second_rate = per_second_rate
        self.__min_duration_ms_between_requests = min_duration_ms_between_requests
        self.__last_request_time = 0
        self.__request_times = [0] * per_second_rate
        self.__curr_idx = 0

    @contextlib.asynccontextmanager
    async def acquire(self, timeout_ms=0):
        enter_ms = timestamp_ms()
        while True:
            now = timestamp_ms()
            if now - enter_ms > timeout_ms > 0:
                raise RateLimiterTimeout()
            if now - self.__last_request_time <= self.__min_duration_ms_between_requests:
                sleep_time = self.__last_request_time + self.__min_duration_ms_between_requests - now
                await asyncio.sleep(sleep_time / 1000)
                continue

            if now - self.__request_times[self.__curr_idx] < 1000:
                sleep_time = self.__request_times[self.__curr_idx] + 1000 - now
                await asyncio.sleep(sleep_time / 1000)
                continue

            break

        self.__last_request_time = self.__request_times[self.__curr_idx] = now
        self.__curr_idx = (self.__curr_idx + 1) % self.__per_second_rate
        yield self


async def exchange_facing_worker(url: str, api_key: str, queue: Queue, logger: logging.Logger):
    rate_limiter = RateLimiter(PER_SEC_RATE, DURATION_MS_BETWEEN_REQUESTS)
    timeout_duration = float(os.getenv('API_TIMEOUT', '1.0'))  # Configurable timeout
    async with aiohttp.ClientSession() as session:
        while True:
            request: Request = await queue.get()
            remaining_ttl = REQUEST_TTL_MS - (timestamp_ms() - request.create_time)
            if remaining_ttl <= 0:
                logger.warning(f"ignoring request {request.req_id} from queue due to TTL")
                continue

            try:
                nonce = timestamp_ms()
                async with rate_limiter.acquire(timeout_ms=remaining_ttl):
                    async with async_timeout.timeout(timeout_duration):
                        params = {'api_key': api_key, 'nonce': nonce, 'req_id': request.req_id}
                        response = await session.get(url=url, params=params)
                        response_json = await response.json()
                        if response.status == 200 and response_json['status'] == 'OK':
                            logger.info(f"API response: status {response.status}, response {response_json}")
                        else:
                            logger.warning(f"API response: status {response.status}, response {response_json}")
            except RateLimiterTimeout:
                logger.warning(f"ignoring request {request.req_id} in limiter due to TTL")
            except aiohttp.ClientError as e:
                logger.error(f"Client error for request {request.req_id}: {str(e)}")
            except asyncio.TimeoutError as e:
                logger.error(f"Client error for request {request.req_id}: {str(e)}")
            except json.JSONDecodeError:
                logger.error(f"JSON parsing error for request {request.req_id}")
            except Exception as e:
                logger.error(f"Unexpected error for request {request.req_id}: {str(e)}")


class Request:
    def __init__(self, req_id):
        self.req_id = req_id
        self.create_time = timestamp_ms()


def main():
    url = "http://127.0.0.1:9999/api/request"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    queue = asyncio.Queue()

    logger = configure_logger()
    loop.create_task(generate_requests(queue=queue))

    for api_key in VALID_API_KEYS:
        loop.create_task(exchange_facing_worker(url=url, api_key=api_key, queue=queue, logger=logger))

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == '__main__':
    main()

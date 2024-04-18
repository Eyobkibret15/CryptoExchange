# CryptoExchange
 cryptocurrencies exchange, SimpleCryptoExchange (aka SCEx). SCEx provides a REST-based API for trading, and implements a simple rate limiting protocol 

### Key Changes

1. **Enhanced Logging**:
   - Implemented dynamic logging levels controlled by environment variables and introduced a rotating file handler to manage logs more effectively, facilitating better maintenance and debugging.

2. **Refined Error Handling**:
   - Broadened error handling to capture and log specific exceptions like `aiohttp.ClientError`, `json.JSONDecodeError`, and `asyncio.TimeoutError`, enhancing the robustness of the client.

3. **Precision in Rate Limiting**:
   - Improved the precision in rate limiting calculations within the `RateLimiter` class, minimizing unnecessary delays and optimizing the usage of available request capacity.

### Enhanced Main Function

- **Event Loop Management**:
  - Switched from using `asyncio.get_event_loop()` to `asyncio.new_event_loop()` and explicitly setting it with `asyncio.set_event_loop()`. This ensures that each run starts with a clean state in the event loop, reducing potential conflicts or errors in environments where the event loop's state may be compromised.

- **Queue Implementation**:
  - Clarified the use of `asyncio.Queue()` for all queue operations, reinforcing the asynchronous nature of the application and ensuring compatibility with the async tasks.

- **Graceful Shutdown**:
  - Added a `try...finally` block around the event loop's `run_forever()` call. This ensures that the application shuts down gracefully, properly closing the event loop and cleaning up asynchronous generators, which is crucial for resource management and application stability.

### Design Choices

- **Asynchronous Programming**:
  - Chose to use asyncio over multithreading due to its efficiency in handling I/O-bound tasks, such as network requests, and its ability to manage high concurrency without significant overhead.

- **Configurable Logging and Timeout Settings**:
  - Utilized environment variables (`LOG_LEVEL`, `API_TIMEOUT`) to allow for easy adjustments of logging verbosity and API timeout settings without modifying the code, catering to different deployment environments or debugging needs.
  - separate the source code with log files.

- **Improved Rate Limiter**:
  - The rate limiter now calculates the exact time until the next allowable request, which helps in making full use of the rate limit without breaches, thus maintaining the service's availability and compliance with the API's constraints.

## Impact on Performance

- **Increased Throughput**:
  - The modifications have enabled the client to approach the maximum rate limit more closely without errors, significantly enhancing throughput.

- **Stability and Reliability**:
  - Enhanced error handling and dynamic configuration lead to a more stable and reliable interaction with the SCEx API, reducing potential downtime and service disruptions.

## Future Enhancements

- **Adaptive Rate Limiting**:
  - Future versions could include adaptive rate limiting based on real-time feedback from the server, allowing the client to adjust request rates dynamically in response to server load or other external factors.
  - revise the configuration setup for time mannered file rotating setup and the backup.

- **Extended Testing Framework**:
  - Expanding the testing framework to cover a wider range of scenarios, including stress and load testing, would further ensure the client's resilience and robustness under various network conditions.

## Conclusion

The refinements to the client demonstrate the advantages of asynchronous programming in maximizing API throughput while adhering to rate limiting protocols. These improvements lay a solid foundation for future enhancements and ensure efficient and reliable API interactions.

---

For inquiries or issues regarding this implementation, please contact [eyob.kibret15@gmail.com](mailto:your-email@email.com).

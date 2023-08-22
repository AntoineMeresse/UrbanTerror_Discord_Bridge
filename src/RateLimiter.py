# Credit : https://stackoverflow.com/a/76846037

# Custom RateLimiter class with dynamic rate limiting values per route
import time
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, requests_limit: int, time_window: int, request_counters : dict, whitelisted_urls : list):
        self.requests_limit = requests_limit
        self.time_window = time_window
        self.request_counters = request_counters
        self.whitelisted_urls = whitelisted_urls

    async def __call__(self, request: Request):
        client_ip = request.client.host
        if (client_ip in self.whitelisted_urls):
            return True

        route_path = request.url.path

        # Get the current timestamp
        current_time = int(time.time())

        # Create a unique key based on client IP and route path
        key = f"{client_ip}:{route_path}"

        # Check if client's request counter exists
        if key not in self.request_counters:
            self.request_counters[key] = {"timestamp": current_time, "count": 1}
        else:
            # Check if the time window has elapsed, reset the counter if needed
            if current_time - self.request_counters[key]["timestamp"] > self.time_window:
                # Reset the counter and update the timestamp
                self.request_counters[key]["timestamp"] = current_time
                self.request_counters[key]["count"] = 1
            else:
                # Check if the client has exceeded the request limit
                if self.request_counters[key]["count"] >= self.requests_limit:
                    raise HTTPException(status_code=429, detail="Too Many Requests")
                else:
                    self.request_counters[key]["count"] += 1

        # Clean up expired client data (optional)
        for k in list(self.request_counters.keys()):
            if current_time - self.request_counters[k]["timestamp"] > self.time_window:
                self.request_counters.pop(k)

        return True
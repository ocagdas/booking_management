from redis import Redis
from rq import Worker

from app.core.settings import get_settings


def main() -> None:
    settings = get_settings()
    worker = Worker(["default"], connection=Redis.from_url(settings.redis_url))
    worker.work()


if __name__ == "__main__":
    main()

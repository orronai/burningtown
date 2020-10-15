from loguru import logger


logger.add(
    'logs.log',
    format='{time:YYYY-MM-DD at HH:mm:ss} | {name} | {message}',
    level='DEBUG',
)

log = logger.bind()

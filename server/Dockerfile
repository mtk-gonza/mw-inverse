FROM python:3.14-slim
WORKDIR /mw-inverse
COPY server/ ./server/
WORKDIR /mw-inverse/server
RUN mkdir -p data
ENV MW_INVERSE_HOST=0.0.0.0
ENV MW_INVERSE_PORT=24500
EXPOSE 24500
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import socket; socket.create_connection(('127.0.0.1',24500),2).close()"
CMD ["python", "main.py"]
